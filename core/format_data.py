import pandas as pd


def load_data(file):
    df = pd.read_csv(file)
    return df


if __name__ == "__main__":
    data = load_data("core/csv/europastat.csv")

    print(
        data[["name", "manOfTheMatch", "teamName", "goal", "tournamentShortName"]].head(
            20
        )
    )
