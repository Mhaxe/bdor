import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface Player {
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
}

interface ApiResponse {
  success: boolean;
  total_players: number;
  players: Player[];
}

const fetchPlayerRankings = async (): Promise<ApiResponse> => {
  const response = await axios.get("/api/rankings/");
  return response.data;
};

function Rankings() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["playerRankings"],
    queryFn: fetchPlayerRankings,
  });

  if (isLoading) {
    return (
      <div className="p-4">
        <div className="text-center py-8">Loading player rankings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="text-center py-8 text-red-500">
          Error loading player rankings:{" "}
          {error instanceof Error ? error.message : "Unknown error"}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <Table>
        <TableCaption>
          {data?.total_players
            ? `Showing ${Math.min(data.total_players, data.players.length)} of ${data.total_players} players`
            : "Player Rankings"}
        </TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">Rank</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Position</TableHead>
            <TableHead>Team</TableHead>
            <TableHead className="text-right">Points</TableHead>
            <TableHead className="text-right">Goals</TableHead>
            <TableHead className="text-right">Assists</TableHead>
            <TableHead className="text-right">Yellow Cards</TableHead>
            <TableHead className="text-right">Red Cards</TableHead>
            <TableHead className="text-right">MOTM</TableHead>
            <TableHead className="text-right">Rating</TableHead>
            <TableHead className="text-right">Appearances</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.players.map((player, index) => (
            <TableRow key={index}>
              <TableCell className="font-medium">{index + 1}</TableCell>
              <TableCell>{player.name}</TableCell>
              <TableCell className="capitalize">{player.position}</TableCell>
              <TableCell className="capitalize">{player.team_name}</TableCell>
              <TableCell className="text-right">
                {player.points.toFixed(2)}
              </TableCell>
              <TableCell className="text-right">{player.goals}</TableCell>
              <TableCell className="text-right">{player.assists}</TableCell>
              <TableCell className="text-right">
                {player.yellow_cards}
              </TableCell>
              <TableCell className="text-right">{player.red_cards}</TableCell>
              <TableCell className="text-right">
                {player.man_of_the_match}
              </TableCell>
              <TableCell className="text-right">{player.rating}</TableCell>
              <TableCell className="text-right">{player.appearances}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export default Rankings;
