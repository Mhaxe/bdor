
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import MainLayout from "@/layouts/MainLayout";

interface PointsContext {
  points_per_goal: number;
  points_per_assist: number;
  points_per_clean_sheet: number;
  points_per_penalty_save: number;
  points_per_penalty_miss: number;
  points_per_yellow_card: number;
  points_per_red_card: number;
  points_per_own_goal: number;
  points_per_2_goals_conceded: number;
  points_per_man_of_the_match: number;
}

interface PointsSystem {
  forward: PointsContext;
  midfielder: PointsContext;
  defender: PointsContext;
  goalkeeper: PointsContext;
}

const competitions = [
  {
    name: "Premier League",
    imageSrc: "/static/competitions/premier-league.webp",
    imageAlt: "Premier League",
  },
  {
    name: "La Liga",
    imageSrc: "/static/competitions/la-liga.webp",
    imageAlt: "La Liga",
  },
  {
    name: "Bundesliga",
    imageSrc: "/static/competitions/bundesliga.webp",
    imageAlt: "Bundesliga",
  },
  {
    name: "Serie A",
    imageSrc: "/static/competitions/serie-a.webp",
    imageAlt: "Serie A",
  },
  {
    name: "Ligue 1",
    imageSrc: "/static/competitions/ligue-1.webp",
    imageAlt: "Ligue 1",
  },
  {
    name: "Champions League",
    imageSrc: "/static/competitions/champions-league.webp",
    imageAlt: "Champions League",
  },
  {
    name: "Europa League",
    imageSrc: "/static/competitions/europa-league.webp",
    imageAlt: "Europa League",
  },
] as const;

interface FAQsApiResponse {
  points_system: PointsSystem;
}

const fetchFaqs = async (): Promise<FAQsApiResponse> => {
  const response = await axios.get("/api/faqs/");
  return response.data;
};
const formatPointsValue = (value: number) => {
  if (value === 0) return "N/A";
  if (value > 0) return `+${value}`;
  return `${value}`;
};

const PointsMatrix = ({ data }: { data: PointsSystem | undefined }) => {
  if (!data) return null;

  const columns = [
    { key: "points_per_goal", label: "Goals" },
    { key: "points_per_assist", label: "Assists" },
    { key: "points_per_clean_sheet", label: "Clean Sheets" },
    { key: "points_per_penalty_save", label: "Penalty Saves" },
    { key: "points_per_penalty_miss", label: "Penalty Misses" },
    { key: "points_per_yellow_card", label: "Yellow Cards" },
    { key: "points_per_red_card", label: "Red Cards" },
    { key: "points_per_own_goal", label: "Own Goals" },
    { key: "points_per_2_goals_conceded", label: "2 Goals Conceded" },
    { key: "points_per_man_of_the_match", label: "Man of the Match" },
  ] as const;

  const rows = [
    { label: "Forward (Striker or Winger)", values: data.forward },
    { label: "Midfielder", values: data.midfielder },
    { label: "Defender", values: data.defender },
    { label: "Keeper", values: data.goalkeeper },
  ] as const;

  return (
    <div className="overflow-x-auto rounded-md border mt-2">
      <table className="w-full text-sm text-left">
        <thead className="bg-muted text-muted-foreground border-b">
          <tr>
            <th className="px-4 py-2 font-medium min-w-56">Position</th>
            {columns.map((column) => (
              <th key={column.key} className="px-4 py-2 font-medium text-right whitespace-nowrap">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y">
          {rows.map((row) => (
            <tr key={row.label} className="hover:bg-muted/50 transition-colors">
              <td className="px-4 py-2 font-medium">{row.label}</td>
              {columns.map((column) => {
                const rawValue = row.values[column.key];
                return (
                  <td key={`${row.label}-${column.key}`} className="px-4 py-2 text-right">
                    <span
                      className={
                        rawValue > 0
                          ? "text-green-600 font-medium"
                          : rawValue < 0
                            ? "text-red-600 font-medium"
                            : "text-muted-foreground"
                      }
                    >
                      {formatPointsValue(rawValue)}
                    </span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

function FAQs() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["faqs"],
    queryFn: fetchFaqs,
  });

  return (
    <MainLayout>
      <div className="w-full max-w-4xl mx-auto p-4 md:p-8 space-y-8">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2">FAQs</h1>
          <p className="text-muted-foreground">
            Learn more about how BalonRank works and how players are scored.
          </p>
        </div>

        {isLoading && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">Loading FAQs...</p>
          </div>
        )}

        {error && (
          <div className="text-center py-12 text-red-500 bg-red-50 rounded-lg p-4">
            <p>Error loading FAQs: {error instanceof Error ? error.message : "Unknown error"}</p>
          </div>
        )}

        {data && (
          <section id="points-system" className="space-y-6">
            <h2 className="text-2xl font-semibold border-b pb-2">Points System</h2>
            <p className="text-muted-foreground">
              Points are awarded differently depending on the player's position. Values shown as N/A do not apply to that position.
            </p>
            <PointsMatrix data={data.points_system} />
          </section>
        )}

        <section id="supported-competitions" className="space-y-6">
          <h2 className="text-2xl font-semibold border-b pb-2">Supported Competitions</h2>
          <p className="text-muted-foreground">
            BalonRank currently tracks player statistics and performances across these elite competitions.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {competitions.map((competition) => (
              <div
                key={competition.name}
                className="flex flex-col items-center justify-center p-4 border rounded-lg bg-card transition-shadow gap-3 text-center"
              >
                <img
                  src={competition.imageSrc}
                  alt={competition.imageAlt}
                  loading="lazy"
                  className="h-16 w-auto object-contain"
                />
                <span className="font-medium text-sm">{competition.name}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </MainLayout>
  );
}

export default FAQs;
