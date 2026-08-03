import * as React from "react";
import type { CSSProperties } from "react";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  type Column,
  type ColumnDef,
  type ColumnFiltersState,
  type ColumnPinningState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  type SortingState,
  type PaginationState,
  useReactTable,
  type VisibilityState,
} from "@tanstack/react-table";
import {
  ChevronDown,
  ChevronRight,
  ChevronUp,
  FilterIcon,
  SearchIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "@/components/ui/combobox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
  InputGroupText,
} from "@/components/ui/input-group";
import { cn } from "@/lib/utils";
import MainLayout from "@/layouts/MainLayout";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ApiResponse {
  success: boolean;
  total_players: number;
  players: Player[];
}

type Player = {
  rank: number;
  rank_change: "up" | "down" | "same";
  previous_rank: number | null;
  name: string;
  position: string;
  points: number;
  goals: number;
  assists: number;
  team_name: string;
  yellow_cards: number;
  red_cards: number;
  man_of_the_match: number;
  rating: number;
  appearances: number;
  player_id: number;
};

type StatKey = "points" | "goals" | "assists" | "rating";

type SheetFiltersState = {
  team: string | null;
  positions: string[];
};

const EMPTY_SHEET_FILTERS: SheetFiltersState = {
  team: null,
  positions: [],
};

const fetchPlayerRankings = async (): Promise<ApiResponse> => {
  const response = await axios.get("/api/rankings/");
  return response.data;
};

// ---------------------------------------------------------------------------
// Design tokens (see spec 1c: "Part-by-part spec — drop-in classes")
// ---------------------------------------------------------------------------

// 01 · HIERARCHY — three weight tiers, not twelve
const TIER1 = "text-[15px] font-bold text-[#08283B]"; // Rank, Player, Points
const TIER2 = "text-[13.5px] font-medium text-gray-700"; // Position/Team, Goals, Assists, Rating
const TIER3 = "text-xs font-normal text-gray-500"; // Yellow, Red, MOTM, Apps

// 04 · NUMERICS — tabular figures
const NUMERIC = "font-mono tabular-nums [font-variant-numeric:slashed-zero]";

// Rank rail colours: 1st → 3rd
const RAIL = ["#FF5A00", "#FF9054", "#FFCCB0"];

const numOrDash = (value: number) => (value === 0 ? "—" : value);

const ratingTintClass = (rating: number) => {
  if (rating >= 7.8) return "bg-emerald-50 text-emerald-700";
  if (rating >= 7.2) return "bg-sky-50 text-sky-800";
  return "bg-gray-100 text-gray-600";
};

const disciplineChipClass = (value: number, tone: "amber" | "red") => {
  if (value === 0) return "text-gray-400";
  return tone === "amber"
      ? "bg-amber-50 text-amber-700"
      : "bg-red-50 text-red-700";
};

// ---------------------------------------------------------------------------
// 03 · TOP THREE — rail + medallion, same row height
// ---------------------------------------------------------------------------

const medallionClass = (rank: number) => {
  if (rank === 1) return "bg-[#08283B] border-[#08283B] text-white";
  if (rank === 2) return "border-orange-500 text-[#08283B]";
  return "border-orange-300 text-[#08283B]";
};

const RankMedallion = ({ rank }: { rank: number }) => {
  if (rank > 3) {
    return (
        <span className="shrink-0 text-sm font-bold tabular-nums text-[#08283B]">
          {rank}
        </span>
    );
  }
  return (
      <span
          className={cn(
              "inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-sm font-bold",
              medallionClass(rank),
          )}
      >
      {rank}
    </span>
  );
};

// ---------------------------------------------------------------------------
// 02 · RANK CHANGE — fixed-width delta pill (shows how far, not where from)
// ---------------------------------------------------------------------------

const RankDeltaBadge = ({
                          rank,
                          previousRank,
                        }: {
  rank: number;
  previousRank: number | null;
}) => {
  if (previousRank === null) {
    return (
        <Badge
            variant="outline"
            className="h-[19px] min-w-[34px] gap-px rounded border-transparent bg-sky-50 px-1.5 font-mono text-[10px] tabular-nums text-sky-700"
        >
          NEW
        </Badge>
    );
  }

  const delta = previousRank - rank; // positive = moved up

  if (delta === 0) {
    return (
        <Badge
            variant="outline"
            className="h-[19px] min-w-[34px] gap-px rounded border-transparent px-1.5 font-mono text-[10px] tabular-nums text-gray-400"
        >
          —
        </Badge>
    );
  }

  const up = delta > 0;
  return (
      <Badge
          variant="outline"
          className={cn(
              "h-[19px] min-w-[34px] gap-px rounded border-transparent px-1.5 font-mono text-[10px] tabular-nums",
              up ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700",
          )}
      >
        {up ? (
            <ChevronUp className="size-2.5" />
        ) : (
            <ChevronDown className="size-2.5" />
        )}
        {Math.abs(delta)}
      </Badge>
  );
};

// ---------------------------------------------------------------------------
// Filter helpers
// ---------------------------------------------------------------------------

const buildFilterSummary = (filters: SheetFiltersState) => {
  const parts: string[] = [];
  if (filters.team) parts.push(`Team: ${filters.team}`);
  if (filters.positions.length > 0) {
    parts.push(
        `Position: ${filters.positions.map((p) => p.toUpperCase()).join(", ")}`,
    );
  }
  return parts.length === 0 ? "Filter players..." : parts.join(" • ");
};

const countActiveFilters = (filters: SheetFiltersState) => {
  let count = 0;
  if (filters.team) count += 1;
  if (filters.positions.length > 0) count += 1;
  return count;
};

// ---------------------------------------------------------------------------
// 05 · HEADER & DENSITY — grouped columns
// PLAYER groups Rank/Player/Position/Team, TOTAL is Points, ATTACKING is
// Goals/Assists, DISCIPLINE is Yellow/Red/MOTM/Apps, FORM is Rating.
// rank_change stays a hidden leaf column purely to drive the movement filter
// (the visible delta pill lives inside the Rank cell).
// ---------------------------------------------------------------------------

const columns: ColumnDef<Player>[] = [
  {
    id: "player-group",
    header: () => <span>Player</span>,
    columns: [
      {
        id: "rank",
        accessorKey: "rank",
        size: 110,
        minSize: 110,
        maxSize: 110,
        header: () => <div className="text-center">Rank</div>,
        enableSorting: false,
        cell: ({ row }) => (
            <div className="flex items-center gap-2">
              <RankMedallion rank={row.getValue("rank")} />
              <RankDeltaBadge
                  rank={row.original.rank}
                  previousRank={row.original.previous_rank}
              />
            </div>
        ),
      },
      {
        accessorKey: "name",
        size: 200,
        minSize: 200,
        header: "Player",
        cell: ({ row }) => (
            <div className={TIER1}>{row.getValue("name")}</div>
        ),
      },
      {
        accessorKey: "position",
        size: 96,
        header: "Pos",
        cell: ({ row }) => (
            <div className={cn(TIER2, "uppercase")}>
              {row.getValue("position")}
            </div>
        ),
        filterFn: (row, columnId, filterValue: string[]) => {
          if (!filterValue || filterValue.length === 0) return true;
          return filterValue.includes(
              row.getValue<string>(columnId)?.toLowerCase(),
          );
        },
      },
      {
        accessorKey: "team_name",
        size: 160,
        header: "Team",
        cell: ({ row }) => (
            <div className={cn(TIER2, "capitalize")}>
              {row.getValue("team_name")}
            </div>
        ),
      },
    ],
  },
  {
    id: "total-group",
    header: () => <span>Total</span>,
    columns: [
      {
        accessorKey: "points",
        header: () => <div className="text-right">Points</div>,
        cell: ({ row }) => {
          const points = parseFloat(row.getValue("points"));
          return (
              <div className={cn(TIER1, NUMERIC, "text-right")}>
                {points.toFixed(2)}
              </div>
          );
        },
      },
    ],
  },
  {
    id: "attacking-group",
    header: () => <span>Attacking</span>,
    columns: [
      {
        accessorKey: "goals",
        header: () => <div className="text-right">G</div>,
        cell: ({ row }) => (
            <div className={cn(TIER2, NUMERIC, "text-right")}>
              {numOrDash(row.getValue("goals"))}
            </div>
        ),
      },
      {
        accessorKey: "assists",
        header: () => <div className="text-right">A</div>,
        cell: ({ row }) => (
            <div className={cn(TIER2, NUMERIC, "text-right")}>
              {numOrDash(row.getValue("assists"))}
            </div>
        ),
      },
    ],
  },
  {
    id: "discipline-group",
    header: () => <span>Discipline</span>,
    columns: [
      {
        accessorKey: "yellow_cards",
        header: () => <div className="text-right">Y</div>,
        cell: ({ row }) => {
          const v = row.getValue<number>("yellow_cards");
          return (
              <div className="text-right">
              <span
                  className={cn(
                      TIER3,
                      NUMERIC,
                      "inline-block rounded px-1.5 py-0.5",
                      disciplineChipClass(v, "amber"),
                  )}
              >
                {numOrDash(v)}
              </span>
              </div>
          );
        },
      },
      {
        accessorKey: "red_cards",
        header: () => <div className="text-right">R</div>,
        cell: ({ row }) => {
          const v = row.getValue<number>("red_cards");
          return (
              <div className="text-right">
              <span
                  className={cn(
                      TIER3,
                      NUMERIC,
                      "inline-block rounded px-1.5 py-0.5",
                      disciplineChipClass(v, "red"),
                  )}
              >
                {numOrDash(v)}
              </span>
              </div>
          );
        },
      },
      {
        accessorKey: "man_of_the_match",
        header: () => <div className="text-right">MOTM</div>,
        cell: ({ row }) => (
            <div className={cn(TIER3, NUMERIC, "text-right")}>
              {numOrDash(row.getValue("man_of_the_match"))}
            </div>
        ),
      },
      {
        accessorKey: "appearances",
        header: () => <div className="text-right">Apps</div>,
        cell: ({ row }) => (
            <div className={cn(TIER3, NUMERIC, "text-right")}>
              {row.getValue("appearances")}
            </div>
        ),
      },
    ],
  },
  {
    id: "form-group",
    header: () => <span>Form</span>,
    columns: [
      {
        accessorKey: "rating",
        header: () => <div className="text-right">Rating</div>,
        cell: ({ row }) => {
          const r = row.getValue<number>("rating");
          return (
              <div className="text-right">
              <span
                  className={cn(
                      TIER2,
                      NUMERIC,
                      "inline-block rounded px-1.5 py-0.5",
                      ratingTintClass(r),
                  )}
              >
                {r.toFixed(2)}
              </span>
              </div>
          );
        },
      },
      // Hidden — drives the All / Rising / Falling toolbar control only.
      {
        accessorKey: "rank_change",
        enableHiding: true,
        filterFn: (row, columnId, filterValue: string[]) => {
          if (!filterValue || filterValue.length === 0) return true;
          return filterValue.includes(row.getValue<string>(columnId));
        },
      },
    ],
  },
];

// ---------------------------------------------------------------------------
// 06 · PINNING & NARROW — pinned column styling shared by the desktop table
// ---------------------------------------------------------------------------

const getPinnedColumnStyles = (column: Column<Player>): CSSProperties => {
  const pinnedSide = column.getIsPinned();
  if (!pinnedSide) return { width: column.getSize() };
  return {
    isolation: "isolate",
    left: `${column.getStart("left")}px`,
    position: "sticky",
    width: column.getSize(),
    zIndex: column.id === "rank" ? 30 : 20,
  };
};

const getPinnedColumnClasses = (column: Column<Player>, isHeader = false) => {
  if (!column.getIsPinned()) return "";
  const backgroundClass = isHeader ? "bg-[#08283B]" : "bg-inherit group-hover:bg-sky-50";
  return cn("relative", !isHeader && "bg-clip-padding overflow-hidden", backgroundClass);
};

// Approximate sticky behaviour for a group header cell whose children
// contain a pinned leaf column (e.g. the "Player" group header spanning the
// pinned Rank + Player columns). Verify this visually against your actual
// column widths — group-level pinning isn't native to the table state.
const getPinnedGroupStyles = (header: {
  subHeaders: { column: Column<Player> }[];
}): CSSProperties => {
  const pinnedSub = header.subHeaders?.find((sh) => sh.column.getIsPinned());
  if (!pinnedSub) return {};
  return {
    position: "sticky",
    left: `${pinnedSub.column.getStart("left")}px`,
    zIndex: 45,
  };
};

// ---------------------------------------------------------------------------
// Mobile card (1b — stat-switcher list instead of a 12-column scroll)
// ---------------------------------------------------------------------------

const STAT_TABS: { key: StatKey; label: string }[] = [
  { key: "points", label: "Points" },
  { key: "goals", label: "Goals" },
  { key: "assists", label: "Assists" },
  { key: "rating", label: "Rating" },
];

const heroValue = (player: Player, stat: StatKey) => {
  if (stat === "points") return player.points.toFixed(2);
  if (stat === "rating") return player.rating.toFixed(2);
  return player[stat];
};

const PlayerCard = ({
                      player,
                      stat,
                      expanded,
                      onToggle,
                    }: {
  player: Player;
  stat: StatKey;
  expanded: boolean;
  onToggle: () => void;
}) => {
  const railColor = player.rank <= 3 ? RAIL[player.rank - 1] : undefined;

  return (
      <div
          className="border-b last:border-b-0"
          style={railColor ? ({ "--rail": railColor } as CSSProperties) : undefined}
      >
        <button
            type="button"
            onClick={onToggle}
            className={cn(
                "flex w-full items-center gap-3 px-4 py-3 text-left",
                railColor && "shadow-[inset_3px_0_0_0_var(--rail)]",
            )}
        >
          <RankMedallion rank={player.rank} />
          <div className="min-w-0 flex-1">
            <div className={TIER1}>{player.name}</div>
            <div className={cn(TIER3, "uppercase")}>
              {player.position} · {player.team_name}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <span className={cn(TIER1, NUMERIC)}>{heroValue(player, stat)}</span>
            <RankDeltaBadge rank={player.rank} previousRank={player.previous_rank} />
          </div>
          {expanded ? (
              <ChevronUp className="size-4 shrink-0 text-gray-400" />
          ) : (
              <ChevronRight className="size-4 shrink-0 text-gray-400" />
          )}
        </button>

        {expanded && (
            <div className="grid grid-cols-3 gap-4 border-t bg-muted/40 px-4 py-4">
              <div>
                <div className="text-[10px] uppercase tracking-[0.08em] text-gray-400">
                  Goals
                </div>
                <div className={cn(TIER1, NUMERIC)}>{numOrDash(player.goals)}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.08em] text-gray-400">
                  Assists
                </div>
                <div className={cn(TIER1, NUMERIC)}>{numOrDash(player.assists)}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.08em] text-gray-400">
                  MOTM
                </div>
                <div className={cn(TIER2, NUMERIC)}>
                  {numOrDash(player.man_of_the_match)}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.08em] text-gray-400">
                  Rating
                </div>
                <span
                    className={cn(
                        TIER1,
                        NUMERIC,
                        "inline-block rounded px-1.5 py-0.5",
                        ratingTintClass(player.rating),
                    )}
                >
              {player.rating.toFixed(2)}
            </span>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.08em] text-gray-400">
                  Yellow
                </div>
                <span
                    className={cn(
                        TIER2,
                        NUMERIC,
                        "inline-block rounded px-1.5 py-0.5",
                        disciplineChipClass(player.yellow_cards, "amber"),
                    )}
                >
              {numOrDash(player.yellow_cards)}
            </span>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.08em] text-gray-400">
                  Red
                </div>
                <span
                    className={cn(
                        TIER2,
                        NUMERIC,
                        "inline-block rounded px-1.5 py-0.5",
                        disciplineChipClass(player.red_cards, "red"),
                    )}
                >
              {numOrDash(player.red_cards)}
            </span>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.08em] text-gray-400">
                  Apps
                </div>
                <div className={cn(TIER3, NUMERIC)}>{player.appearances}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.08em] text-gray-400">
                  Moved
                </div>
                <RankDeltaBadge rank={player.rank} previousRank={player.previous_rank} />
              </div>
            </div>
        )}
      </div>
  );
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

function Rankings() {
  const [filterSheetContainer, setFilterSheetContainer] =
      React.useState<HTMLDivElement | null>(null);

  const {
    data: apiData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["playerRankings"],
    queryFn: fetchPlayerRankings,
  });

  const data = React.useMemo(() => apiData?.players ?? [], [apiData?.players]);

  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({
    rank_change: false,
  });
  const [isFilterSheetOpen, setIsFilterSheetOpen] = React.useState(false);
  const [nameFilterInput, setNameFilterInput] = React.useState("");
  const [appliedFilters, setAppliedFilters] =
      React.useState<SheetFiltersState>(EMPTY_SHEET_FILTERS);
  const [draftFilters, setDraftFilters] =
      React.useState<SheetFiltersState>(EMPTY_SHEET_FILTERS);

  // All / Rising / Falling toolbar tab (replaces the old Movement checkbox
  // list — now lives in the main toolbar per spec 1a).
  const [movementTab, setMovementTab] = React.useState<"all" | "up" | "down">(
      "all",
  );

  // Stat-switcher tab for the narrow-screen card list (spec 1b).
  const [statTab, setStatTab] = React.useState<StatKey>("points");
  const [mobileVisibleCount, setMobileVisibleCount] = React.useState(12);
  const [expandedCards, setExpandedCards] = React.useState<Set<number>>(
      new Set(),
  );

  // Responsive column pinning: pin the first two columns on md+ screens,
  // but disable pinning on smaller screens so the full table can scroll.
  const [columnPinning, setColumnPinning] = React.useState<ColumnPinningState>(
      () => {
        if (typeof window === "undefined") return {};
        const mql = window.matchMedia("(min-width: 768px)");
        return mql.matches ? { left: ["rank", "name"] } : {};
      },
  );

  React.useEffect(() => {
    if (typeof window === "undefined") return;
    const mql = window.matchMedia("(min-width: 768px)");
    const syncColumnPinning = (matches: boolean) => {
      setColumnPinning(matches ? { left: ["rank", "name"] } : {});
    };
    const handleChange = (event: MediaQueryListEvent) => syncColumnPinning(event.matches);

    syncColumnPinning(mql.matches);

    if (typeof mql.addEventListener === "function") {
      mql.addEventListener("change", handleChange);
      return () => mql.removeEventListener("change", handleChange);
    }
    mql.addListener(handleChange);
    return () => mql.removeListener(handleChange);
  }, []);

  const [rowSelection, setRowSelection] = React.useState({});
  const [currentPage, setCurrentPage] = React.useState(1);

  const teamNames = React.useMemo(
      () =>
          [...new Set(data.map((p) => p.team_name))]
              .filter(Boolean)
              .sort((a, b) => a.localeCompare(b)),
      [data],
  );

  const positions = React.useMemo(
      () =>
          [...new Set(data.map((p) => p.position?.toLowerCase()))]
              .filter(Boolean)
              .sort((a, b) => a.localeCompare(b)),
      [data],
  );

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 50,
  });

  const table = useReactTable({
    data,
    columns,
    onPaginationChange: setPagination,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      columnPinning,
      rowSelection,
      pagination,
    },
  });

  React.useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      table.getColumn("name")?.setFilterValue(nameFilterInput || undefined);
      table.setPageIndex(0);
      setCurrentPage(1);
      setMobileVisibleCount(12);
    }, 200);
    return () => window.clearTimeout(timeoutId);
  }, [nameFilterInput, table]);

  React.useEffect(() => {
    table.getColumn("team_name")?.setFilterValue(appliedFilters.team ?? undefined);
  }, [appliedFilters.team, table]);

  React.useEffect(() => {
    table
        .getColumn("position")
        ?.setFilterValue(
            appliedFilters.positions.length > 0 ? appliedFilters.positions : undefined,
        );
  }, [appliedFilters.positions, table]);

  React.useEffect(() => {
    const movements = movementTab === "all" ? undefined : [movementTab];
    table.getColumn("rank_change")?.setFilterValue(movements);
  }, [movementTab, table]);

  React.useEffect(() => {
    table.setPageIndex(0);
    setCurrentPage(1);
    setMobileVisibleCount(12);
  }, [appliedFilters, movementTab, table]);

  const scrollToTop = React.useCallback(() => {
    try {
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch {
      // ignore — window may be unavailable in some environments
    }
  }, []);

  const activeFilterCount = React.useMemo(
      () => countActiveFilters(appliedFilters),
      [appliedFilters],
  );
  const filterSummary = React.useMemo(
      () => buildFilterSummary(appliedFilters),
      [appliedFilters],
  );

  const handleFilterSheetOpenChange = React.useCallback(
      (open: boolean) => {
        if (open) setDraftFilters(appliedFilters);
        setIsFilterSheetOpen(open);
      },
      [appliedFilters],
  );

  const handleApplyFilters = React.useCallback(() => {
    setAppliedFilters({
      team: draftFilters.team,
      positions: [...draftFilters.positions].sort(),
    });
    setIsFilterSheetOpen(false);
  }, [draftFilters]);

  const handleClearDraftFilters = React.useCallback(() => {
    setDraftFilters(EMPTY_SHEET_FILTERS);
  }, []);

  // Rows for the narrow-screen card list: same filtered rows as the table,
  // re-sorted by whichever stat tab is active, sliced to the "load next 12"
  // window.
  //
  // Key the memo on the filtered row model itself, never on the filter inputs
  // (movementTab / nameFilterInput / appliedFilters). Those are pushed into the
  // table from effects, so they change one render *before* the filter is
  // actually applied — memoising on them yields a list that lags a full
  // interaction behind. getFilteredRowModel() is memoised inside the table, so
  // this reference changes exactly when the filtered result does.
  const filteredRows = table.getFilteredRowModel().rows;
  const mobileSortedRows = React.useMemo(
      () =>
          filteredRows
              .map((r) => r.original)
              .sort((a, b) => b[statTab] - a[statTab]),
      [filteredRows, statTab],
  );

  const mobileVisibleRows = mobileSortedRows.slice(0, mobileVisibleCount);

  const toggleCardExpanded = (playerId: number) => {
    setExpandedCards((prev) => {
      const next = new Set(prev);
      if (next.has(playerId)) next.delete(playerId);
      else next.add(playerId);
      return next;
    });
  };

  if (isLoading) {
    return (
        <div className="w-full p-4">
          <div className="text-center py-8">Loading player data...</div>
        </div>
    );
  }

  if (error) {
    return (
        <div className="w-full p-4">
          <div className="text-center py-8 text-red-500">
            Error loading player data:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </div>
        </div>
    );
  }

  return (
      <MainLayout>
        <div className="w-full">
          {/* Toolbar --------------------------------------------------------*/}
          <div className="pb-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <InputGroup className="h-11 flex-1 rounded-lg border-2 has-[[data-slot=input-group-control]:focus-visible]:border-blue-500 has-[[data-slot=input-group-control]:focus-visible]:ring-0">
                <InputGroupAddon align="inline-start">
                  <InputGroupText>
                    <SearchIcon className="size-4" />
                  </InputGroupText>
                </InputGroupAddon>
                <InputGroupInput
                    aria-label="Filter players by name"
                    placeholder="Search players..."
                    value={nameFilterInput}
                    onChange={(event) => setNameFilterInput(event.target.value)}
                    className="text-sm"
                />
              </InputGroup>

              {/* Active filter chips */}
              {appliedFilters.team && (
                  <Badge
                      variant="secondary"
                      className="h-9 shrink-0 gap-1.5 rounded-full px-3 text-sm font-normal"
                  >
                    Team: {appliedFilters.team}
                    <button
                        type="button"
                        aria-label="Remove team filter"
                        onClick={() => setAppliedFilters((prev) => ({ ...prev, team: null }))}
                        className="text-muted-foreground hover:text-foreground"
                    >
                      ×
                    </button>
                  </Badge>
              )}
              {appliedFilters.positions.length > 0 && (
                  <Badge
                      variant="secondary"
                      className="h-9 shrink-0 gap-1.5 rounded-full px-3 text-sm font-normal"
                  >
                    Position: {appliedFilters.positions.map((p) => p.toUpperCase()).join(", ")}
                    <button
                        type="button"
                        aria-label="Remove position filter"
                        onClick={() =>
                            setAppliedFilters((prev) => ({ ...prev, positions: [] }))
                        }
                        className="text-muted-foreground hover:text-foreground"
                    >
                      ×
                    </button>
                  </Badge>
              )}
              {activeFilterCount > 0 && (
                  <button
                      type="button"
                      onClick={() => setAppliedFilters(EMPTY_SHEET_FILTERS)}
                      className="text-sm text-muted-foreground underline-offset-2 hover:underline"
                  >
                    Clear all
                  </button>
              )}

              <div className="flex items-center gap-3 sm:ml-auto">
                {/* All / Rising / Falling */}
                <div className="flex h-9 items-center rounded-lg border-2 p-0.5">
                  {(["all", "up", "down"] as const).map((key) => (
                      <button
                          key={key}
                          type="button"
                          onClick={() => setMovementTab(key)}
                          className={cn(
                              "rounded-md px-3 py-1 text-sm font-medium capitalize transition-colors",
                              movementTab === key
                                  ? "bg-[#08283B] text-white"
                                  : "text-muted-foreground hover:text-foreground",
                          )}
                      >
                        {key === "all" ? "All" : key === "up" ? "Rising" : "Falling"}
                      </button>
                  ))}
                </div>

                <span className="hidden text-xs text-muted-foreground sm:inline">
                {table.getFilteredRowModel().rows.length} / {apiData?.total_players ?? 0}
              </span>

                <Sheet open={isFilterSheetOpen} onOpenChange={handleFilterSheetOpenChange}>
                  <Button
                      type="button"
                      variant="outline"
                      aria-label="Open filters"
                      onClick={() => handleFilterSheetOpenChange(true)}
                      className={cn(
                          "relative h-11 w-11 shrink-0 rounded-lg border-2 p-0 sm:w-auto sm:min-w-[112px] sm:justify-between sm:px-3",
                          activeFilterCount > 0 && "border-blue-500/40",
                      )}
                  >
                  <span className="flex items-center gap-2">
                    <FilterIcon className="size-4" />
                    <span className="hidden sm:inline">Filters</span>
                  </span>
                    {activeFilterCount > 0 && (
                        <span className="absolute -right-1.5 -top-1.5 flex size-5 items-center justify-center rounded-full bg-orange-500 text-[11px] font-semibold text-white sm:static sm:ml-1">
                      {activeFilterCount}
                    </span>
                    )}
                  </Button>

                  <SheetContent
                      ref={setFilterSheetContainer}
                      side="right"
                      className="overflow-x-hidden sm:max-w-xl"
                  >
                    <SheetHeader>
                      <SheetTitle>Filter rankings</SheetTitle>
                      <SheetDescription className="truncate">
                        {activeFilterCount > 0 ? filterSummary : "Narrow down players"}
                      </SheetDescription>
                    </SheetHeader>

                    <div className="flex flex-1 flex-col gap-6 overflow-x-hidden overflow-y-auto py-2">
                      <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium">Team</label>
                        <Combobox
                            value={draftFilters.team}
                            onValueChange={(value: string | null) =>
                                setDraftFilters((prev) => ({ ...prev, team: value }))
                            }
                            items={teamNames}
                        >
                          <ComboboxInput
                              placeholder="Filter teams..."
                              showClear={!!draftFilters.team}
                              className="w-full rounded-lg border-2 has-[[data-slot=input-group-control]:focus-visible]:border-blue-500 has-[[data-slot=input-group-control]:focus-visible]:ring-0"
                          />
                          <ComboboxContent container={filterSheetContainer}>
                            <ComboboxEmpty>No teams found.</ComboboxEmpty>
                            <ComboboxList>
                              {(team: string) => (
                                  <ComboboxItem key={team} value={team}>
                                    {team}
                                  </ComboboxItem>
                              )}
                            </ComboboxList>
                          </ComboboxContent>
                        </Combobox>
                      </div>

                      <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium">Position</label>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                                variant="outline"
                                className="h-10 w-full justify-between rounded-lg border-2 focus-visible:border-blue-500 focus-visible:ring-0 focus-visible:outline-none"
                            >
                              {draftFilters.positions.length === 0
                                  ? "Select positions"
                                  : draftFilters.positions.map((p) => p.toUpperCase()).join(", ")}
                              <ChevronDown className="ml-2 size-4 opacity-50" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent className="w-56">
                            <DropdownMenuLabel>Position</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            {positions.map((pos) => (
                                <DropdownMenuCheckboxItem
                                    key={pos}
                                    className="uppercase"
                                    indicatorSide="right"
                                    checked={draftFilters.positions.includes(pos)}
                                    onCheckedChange={(checked) => {
                                      setDraftFilters((prev) => ({
                                        ...prev,
                                        positions: checked
                                            ? [...prev.positions, pos]
                                            : prev.positions.filter((p) => p !== pos),
                                      }));
                                    }}
                                >
                                  {pos.toUpperCase()}
                                </DropdownMenuCheckboxItem>
                            ))}
                            {draftFilters.positions.length > 0 && (
                                <>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuCheckboxItem
                                      indicatorSide="right"
                                      checked={false}
                                      onCheckedChange={() =>
                                          setDraftFilters((prev) => ({ ...prev, positions: [] }))
                                      }
                                  >
                                    Clear
                                  </DropdownMenuCheckboxItem>
                                </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>

                    <SheetFooter>
                      <Button onClick={handleApplyFilters}>Apply</Button>
                      <Button variant="outline" onClick={() => handleFilterSheetOpenChange(false)}>
                        Cancel
                      </Button>
                      <Button
                          variant="ghost"
                          onClick={handleClearDraftFilters}
                          disabled={countActiveFilters(draftFilters) === 0}
                      >
                        Clear all
                      </Button>
                    </SheetFooter>
                  </SheetContent>
                </Sheet>
              </div>
            </div>
          </div>

          {/* Desktop table ---------------------------------------------------*/}
          <div className="hidden overflow-x-auto rounded-md border md:block">
            <Table className="min-w-max border-separate border-spacing-0">
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                    <TableRow key={headerGroup.id} className="hover:bg-transparent">
                      {headerGroup.headers.map((header) => {
                        const isGroupHeader = header.subHeaders && header.subHeaders.length > 0;
                        return (
                            <TableHead
                                key={header.id}
                                colSpan={header.colSpan}
                                className={cn(
                                    getPinnedColumnClasses(header.column, true),
                                    "border-b border-white/10 bg-[#08283B] text-white/70",
                                    isGroupHeader
                                        ? "h-7 text-[10px] font-normal uppercase tracking-[0.08em] text-white/50"
                                        : "h-10 text-[11px] font-medium uppercase tracking-[0.08em] text-white/80",
                                )}
                                style={{
                                  ...getPinnedColumnStyles(header.column),
                                  ...(isGroupHeader ? getPinnedGroupStyles(header) : {}),
                                  zIndex: header.column.id === "rank" ? 50 : 40,
                                }}
                            >
                              {header.isPlaceholder
                                  ? null
                                  : flexRender(header.column.columnDef.header, header.getContext())}
                            </TableHead>
                        );
                      })}
                    </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows?.length ? (
                    table.getRowModel().rows.map((row) => {
                      const rank = row.original.rank;
                      const railColor = rank <= 3 ? RAIL[rank - 1] : undefined;
                      return (
                          <TableRow
                              key={row.id}
                              data-state={row.getIsSelected() && "selected"}
                              style={
                                railColor ? ({ "--rail": railColor } as CSSProperties) : undefined
                              }
                              className={cn(
                                  "group h-[52px]",
                                  row.index % 2 === 0 ? "bg-background" : "bg-[#F9FAFB]",
                                  "hover:bg-sky-50",
                                  railColor && "shadow-[inset_3px_0_0_0_var(--rail)]",
                              )}
                          >
                            {row.getVisibleCells().map((cell) => (
                                <TableCell
                                    key={cell.id}
                                    className={cn(
                                        getPinnedColumnClasses(cell.column),
                                        "border-b border-border/70",
                                    )}
                                    style={getPinnedColumnStyles(cell.column)}
                                >
                                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                </TableCell>
                            ))}
                          </TableRow>
                      );
                    })
                ) : (
                    <TableRow>
                      <TableCell
                          colSpan={table.getVisibleLeafColumns().length}
                          className="h-24 text-center"
                      >
                        No results.
                      </TableCell>
                    </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {/* Desktop pagination ------------------------------------------------*/}
          <div className="hidden flex-col items-center justify-end gap-4 py-4 md:flex md:flex-row">
            <div className="flex flex-col items-center gap-4 md:flex-row">
              <div className="space-x-2">
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      table.previousPage();
                      scrollToTop();
                    }}
                    disabled={!table.getCanPreviousPage()}
                >
                  Previous
                </Button>
                <Button
                    size="sm"
                    onClick={() => {
                      table.nextPage();
                      scrollToTop();
                    }}
                    disabled={!table.getCanNextPage()}
                >
                  Next
                </Button>
              </div>
              <div className="text-sm text-muted-foreground">
                Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
              </div>
              <form
                  className="flex items-center gap-2"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const pageIndex = currentPage - 1;
                    if (currentPage > 0 && currentPage <= table.getPageCount()) {
                      table.setPageIndex(pageIndex);
                      scrollToTop();
                    }
                  }}
              >
                <span className="text-sm text-muted-foreground">Go to:</span>
                <div className="flex gap-2">
                  <Input
                      type="number"
                      min="1"
                      max={table.getPageCount()}
                      value={currentPage || ""}
                      onChange={(e) => setCurrentPage(+e.target.value)}
                      onBlur={() => {
                        if (currentPage < 1 || currentPage > table.getPageCount()) {
                          setCurrentPage(1);
                        }
                      }}
                      className="w-16 rounded-lg border-2"
                  />
                  <Button type="submit" size="sm" className="rounded-lg">
                    Go
                  </Button>
                </div>
              </form>
            </div>
          </div>

          {/* Narrow-screen card list ------------------------------------------*/}
          <div className="rounded-xl border md:hidden">
            <div className="flex flex-col gap-3 bg-[#08283B] p-3">
              <div className="flex items-center gap-2 rounded-lg bg-white/10 px-3 py-2">
                <SearchIcon className="size-4 text-white/60" />
                <input
                    aria-label="Search players"
                    placeholder="Search players"
                    value={nameFilterInput}
                    onChange={(event) => setNameFilterInput(event.target.value)}
                    className="w-full bg-transparent text-sm text-white placeholder:text-white/50 focus:outline-none"
                />
                <button
                    type="button"
                    aria-label="Open filters"
                    onClick={() => handleFilterSheetOpenChange(true)}
                    className="relative flex size-8 shrink-0 items-center justify-center rounded-lg bg-orange-500 text-white"
                >
                  <FilterIcon className="size-4" />
                  {activeFilterCount > 0 && (
                      <span className="absolute -right-1 -top-1 flex size-4 items-center justify-center rounded-full bg-white text-[10px] font-semibold text-orange-600">
                    {activeFilterCount}
                  </span>
                  )}
                </button>
              </div>

              <div className="flex gap-1 overflow-x-auto">
                {STAT_TABS.map((tab) => (
                    <button
                        key={tab.key}
                        type="button"
                        onClick={() => {
                          setStatTab(tab.key);
                          setMobileVisibleCount(12);
                        }}
                        className={cn(
                            "shrink-0 rounded-md px-3 py-1.5 text-sm font-medium",
                            statTab === tab.key
                                ? "bg-white text-[#08283B]"
                                : "text-white/60 hover:text-white",
                        )}
                    >
                      {tab.label}
                    </button>
                ))}
              </div>
            </div>

            {mobileVisibleRows.length ? (
                <div className="divide-y">
                  {mobileVisibleRows.map((player) => (
                      <PlayerCard
                          key={player.player_id}
                          player={player}
                          stat={statTab}
                          expanded={expandedCards.has(player.player_id)}
                          onToggle={() => toggleCardExpanded(player.player_id)}
                      />
                  ))}
                </div>
            ) : (
                <div className="p-8 text-center text-sm text-muted-foreground">No results.</div>
            )}

            {mobileVisibleCount < mobileSortedRows.length && (
                <div className="flex justify-center border-t p-4">
                  <Button
                      variant="outline"
                      onClick={() => setMobileVisibleCount((prev) => prev + 12)}
                  >
                    Load next 12
                  </Button>
                </div>
            )}
          </div>
        </div>
      </MainLayout>
  );
}

export default Rankings;