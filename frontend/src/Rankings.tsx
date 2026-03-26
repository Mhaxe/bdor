import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  type ColumnDef,
  type ColumnFiltersState,
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
import { ArrowUp, ArrowDown, Circle, ChevronDown } from "lucide-react";

import { Button } from "@/components/ui/button";
// import { Checkbox } from "@/components/ui/checkbox";
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

interface ApiResponse {
  success: boolean;
  total_players: number;
  players: Player[];
}

const fetchPlayerRankings = async (): Promise<ApiResponse> => {
  const response = await axios.get("/api/rankings/");
  return response.data;
};

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

const PreviousRankDisplay = ({
  previousRank,
}: {
  previousRank: number | null;
}) => {
  if (previousRank === null) return null;
  return <span className="text-orange-400 opacity-70">{previousRank}</span>;
};

const RankChangeIcon = ({
  rankChange,
  previousRank,
}: {
  rankChange: "up" | "down" | "same";
  previousRank: number | null;
}) => {
  switch (rankChange) {
    case "up":
      return (
        <div className="flex items-center gap-2">
          <ArrowUp className="w-4 h-4 text-green-600" />
          <PreviousRankDisplay previousRank={previousRank} />
        </div>
      );
    case "down":
      return (
        <div className="flex items-center gap-2">
          <ArrowDown className="w-4 h-4 text-red-600" />
          <PreviousRankDisplay previousRank={previousRank} />
        </div>
      );
    case "same":
      return (
        <div className="flex items-center gap-2">
          <Circle className="w-2 h-2 text-gray-500 fill-gray-500" />
          <PreviousRankDisplay previousRank={previousRank} />
        </div>
      );
    default:
      return null;
  }
};

const columns: ColumnDef<Player>[] = [
  // {
  //   id: "select",
  //   header: ({ table }) => (
  //     <Checkbox
  //       checked={
  //         table.getIsAllPageRowsSelected() ||
  //         (table.getIsSomePageRowsSelected() && "indeterminate")
  //       }
  //       onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
  //       aria-label="Select all"
  //     />
  //   ),
  //   cell: ({ row }) => (
  //     <Checkbox
  //       checked={row.getIsSelected()}
  //       onCheckedChange={(value) => row.toggleSelected(!!value)}
  //       aria-label="Select row"
  //     />
  //   ),
  //   enableSorting: false,
  //   enableHiding: false,
  // },
  {
    id: "rank",
    accessorKey: "rank",
    header: () => <div className="text-center w-28">Rank</div>,
    cell: ({ row }) => (
      <div className="flex items-center justify-center gap-2 w-28">
        <span className="font-medium">{row.getValue("rank")}</span>
        <RankChangeIcon
          rankChange={row.original.rank_change}
          previousRank={row.original.previous_rank}
        />
      </div>
    ),
    enableSorting: false,
  },
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => <div>{row.getValue("name")}</div>,
  },
  {
    accessorKey: "position",
    header: "Position",
    cell: ({ row }) => (
      <div className="capitalize">{row.getValue("position")}</div>
    ),
    filterFn: (row, columnId, filterValue: string[]) => {
      if (!filterValue || filterValue.length === 0) return true;
      return filterValue.includes(row.getValue<string>(columnId)?.toLowerCase());
    },
  },
  {
    accessorKey: "team_name",
    header: "Team",
    cell: ({ row }) => (
      <div className="capitalize">{row.getValue("team_name")}</div>
    ),
  },
  {
    accessorKey: "points",
    header: () => <div className="text-right">Points</div>,
    cell: ({ row }) => {
      const points = parseFloat(row.getValue("points"));
      return <div className="text-right font-medium">{points.toFixed(2)}</div>;
    },
  },
  {
    accessorKey: "goals",
    header: () => <div className="text-right">Goals</div>,
    cell: ({ row }) => (
      <div className="text-right">{row.getValue("goals")}</div>
    ),
  },
  {
    accessorKey: "assists",
    header: () => <div className="text-right">Assists</div>,
    cell: ({ row }) => (
      <div className="text-right">{row.getValue("assists")}</div>
    ),
  },
  {
    accessorKey: "yellow_cards",
    header: () => <div className="text-right">Yellow Cards</div>,
    cell: ({ row }) => (
      <div className="text-right">{row.getValue("yellow_cards")}</div>
    ),
  },
  {
    accessorKey: "red_cards",
    header: () => <div className="text-right">Red Cards</div>,
    cell: ({ row }) => (
      <div className="text-right">{row.getValue("red_cards")}</div>
    ),
  },
  {
    accessorKey: "man_of_the_match",
    header: () => <div className="text-right">MOTM</div>,
    cell: ({ row }) => (
      <div className="text-right">{row.getValue("man_of_the_match")}</div>
    ),
  },
  {
    accessorKey: "rating",
    header: () => <div className="text-right">Rating</div>,
    cell: ({ row }) => (
      <div className="text-right">{row.getValue("rating")}</div>
    ),
  },
  {
    accessorKey: "appearances",
    header: () => <div className="text-right">Appearances</div>,
    cell: ({ row }) => (
      <div className="text-right">{row.getValue("appearances")}</div>
    ),
  },
];

import MainLayout from "@/layouts/MainLayout"

function Rankings() {
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
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    [],
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = React.useState({});
  const [currentPage, setCurrentPage] = React.useState(1);
  const [nameFilterInput, setNameFilterInput] = React.useState("");
  const [teamFilter, setTeamFilter] = React.useState<string | null>(null);
  const [positionFilter, setPositionFilter] = React.useState<string[]>([]);

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
      rowSelection,
      pagination,
    },
  });

  React.useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      table.getColumn("name")?.setFilterValue(nameFilterInput);
    }, 200);
    return () => window.clearTimeout(timeoutId);
  }, [nameFilterInput, table]);

  React.useEffect(() => {
    table.getColumn("team_name")?.setFilterValue(teamFilter ?? undefined);
  }, [teamFilter, table]);

  React.useEffect(() => {
    table
      .getColumn("position")
      ?.setFilterValue(positionFilter.length > 0 ? positionFilter : undefined);
  }, [positionFilter, table]);

  const scrollToTop = React.useCallback(() => {
    try {
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (_e) { // eslint-disable-line @typescript-eslint/no-unused-vars
      // fallback for environments where window might be undefined
      // ignore silently
    }
  }, []);

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
      <div className="flex flex-wrap items-center justify-center gap-2 pb-4">
        <Input
          placeholder="Filter names..."
          value={nameFilterInput}
          onChange={(event) => setNameFilterInput(event.target.value)}
          className="w-full max-w-xs rounded-lg border-2"
        />
        <Combobox
          value={teamFilter}
          onValueChange={(value) => setTeamFilter(value as string | null)}
          items={teamNames}
        >
          <ComboboxInput
            placeholder="Filter teams..."
            showClear={!!teamFilter}
            className="w-full max-w-xs rounded-lg border-2 has-[[data-slot=input-group-control]:focus-visible]:border-blue-500 has-[[data-slot=input-group-control]:focus-visible]:ring-0"
          />
          <ComboboxContent>
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
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="min-w-[120px] justify-between rounded-lg border-2 focus-visible:border-blue-500 focus-visible:ring-0 focus-visible:outline-none">
              {positionFilter.length === 0
                ? "Position"
                : positionFilter.map((p) => p.toUpperCase()).join(", ")}
              <ChevronDown className="ml-2 h-4 w-4 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-36">
            <DropdownMenuLabel>Position</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {positions.map((pos) => (
              <DropdownMenuCheckboxItem
                key={pos}
                className="uppercase"
                checked={positionFilter.includes(pos)}
                onCheckedChange={(checked) => {
                  setPositionFilter((prev) =>
                    checked ? [...prev, pos] : prev.filter((p) => p !== pos)
                  );
                }}
              >
                {pos.toUpperCase()}
              </DropdownMenuCheckboxItem>
            ))}
            {positionFilter.length > 0 && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuCheckboxItem
                  checked={false}
                  onCheckedChange={() => setPositionFilter([])}
                  className="text-muted-foreground"
                >
                  Clear
                </DropdownMenuCheckboxItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex flex-col md:flex-row items-center justify-end gap-4 py-4">
        {/* Commented out selection count UI per request. If you want it back,
            uncomment the block below. */}
        {/**
        <div className="text-muted-foreground text-sm order-3 md:order-1">
          {table.getFilteredSelectedRowModel().rows.length} of {" "}
          {table.getFilteredRowModel().rows.length} row(s) selected.
        </div>
        */}
        <div className="flex flex-col md:flex-row items-center gap-4">
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
            Page {table.getState().pagination.pageIndex + 1} of{" "}
            {table.getPageCount()}
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
                onChange={(e) => {
                  const value = +e.target.value;
                  setCurrentPage(value);
                }}
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
      </div>
    </MainLayout>
  );
}

export default Rankings;
