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
import { ChevronDown } from "lucide-react";

import { Button } from "@/components/ui/button";
// import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
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
    header: () => <div className="text-center w-20">Rank</div>,
    cell: ({ row }) => (
      <div className="text-center font-medium w-20">{row.getValue("rank")}</div>
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

function Rankings() {
  const {
    data: apiData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["playerRankings"],
    queryFn: fetchPlayerRankings,
  });

  const data = apiData?.players ?? [];

  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    [],
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = React.useState({});
  const [currentPage, setCurrentPage] = React.useState(1);
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
    <div className="w-full p-4">
      <div className="flex items-center py-4">
        <Input
          placeholder="Filter names..."
          value={(table.getColumn("name")?.getFilterValue() as string) ?? ""}
          onChange={(event) =>
            table.getColumn("name")?.setFilterValue(event.target.value)
          }
          className="max-w-sm"
        />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="ml-auto">
              Columns <ChevronDown />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {table
              .getAllColumns()
              .filter((column) => column.getCanHide())
              .map((column) => {
                return (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    className="capitalize"
                    checked={column.getIsVisible()}
                    onCheckedChange={(value) =>
                      column.toggleVisibility(!!value)
                    }
                  >
                    {column.id}
                  </DropdownMenuCheckboxItem>
                );
              })}
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
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-4">
        <div className="text-muted-foreground text-sm order-3 md:order-1">
          {table.getFilteredSelectedRowModel().rows.length} of{" "}
          {table.getFilteredRowModel().rows.length} row(s) selected.
        </div>
        <div className="flex flex-col md:flex-row items-center gap-4 w-full md:w-auto order-1 md:order-2">
          <div className="space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              Next
            </Button>
          </div>
          <div className="text-sm text-muted-foreground">
            Page {table.getState().pagination.pageIndex + 1} of{" "}
            {table.getPageCount()}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Go to:</span>
            <Input
              type="number"
              min="1"
              max={table.getPageCount()}
              value={currentPage || ""}
              onChange={(e) => {
                const value = +e.target.value;
                const pageIndex = value - 1;
                setCurrentPage(value); // if value is 0 the input field will be empty
                if (value > 0 && value <= table.getPageCount()) {
                  table.setPageIndex(pageIndex);
                }
              }}
              onBlur={() => {
                if (currentPage < 1 || currentPage > table.getPageCount()) {
                  setCurrentPage(1); // default to first page if anything is invalid
                } else {
                  setCurrentPage(currentPage);
                }
              }}
              className="w-16"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Rankings;
