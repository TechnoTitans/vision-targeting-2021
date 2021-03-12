import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

df = pd.read_csv("data/DistanceWithLensCorrection2.csv")

for name, df_group in df.groupby("Correction_Strength"):
    # 1.1, 1.25, 1.3, 1.6, 1.75 is best
    # 1.1 best with correction values: 0.22018465 -10.68580068
    if name in [1.1, 1.25, 1.3, 1.6, 1.75]:
        df_group = df_group.reset_index()
        df_group["Error"] = df_group["Real_Distance"] - df_group["Predicted_Distance"]

        line_params = np.polyfit(df_group["Predicted_Distance"], df_group["Error"], 1)
        print(f"Correction Factor: {name}, Line Fit Params: {line_params}")

        df_group["Correction_Factor"] = ((df_group["Predicted_Distance"] * line_params[0]) + line_params[1])
        df_group["Corrected_Distance"] = df_group["Predicted_Distance"] + df_group["Correction_Factor"]
        df_group["Corrected_Error"] = df_group["Real_Distance"] - df_group["Corrected_Distance"]

        plt.plot(df_group["Predicted_Distance"], df_group["Error"], label=name)
        plt.plot(df_group["Predicted_Distance"], df_group["Corrected_Error"], label=name)

        for i in range(len(df_group["Predicted_Distance"])):
            plt.text(df_group["Predicted_Distance"][i], df_group["Error"][i], name)
            plt.text(df_group["Predicted_Distance"][i], df_group["Corrected_Error"][i], name)

plt.legend(bbox_to_anchor=(1.05, 1))
plt.grid()
plt.xticks(np.arange(60, 166, 5))
plt.xlabel("Predicted Distance")
plt.ylabel("Error")
plt.title("Percent Error Over Various Distances for Different Correction Strengths")
plt.show()
