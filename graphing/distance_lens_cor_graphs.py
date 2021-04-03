import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

df = pd.read_csv("../data/DistanceWithLensCorrection2.csv")

for name, df_group in df.groupby("Correction_Strength"):
    if name > 0:
        df_group = df_group.reset_index()

        plt.plot(df_group["Real_Distance"], df_group["Percent_Error"]*100, label=name)

        for i in range(len(df_group["Real_Distance"])):
            plt.text(df_group["Real_Distance"][i], df_group["Percent_Error"][i]*100, name)

plt.legend(bbox_to_anchor=(1.05, 1))
plt.grid()
plt.xticks(np.arange(60, 166, 5))
plt.xlabel("Real Distance")
plt.ylabel("Percent Error")
plt.title("Percent Error Over Various Distances for Different Correction Strengths")
plt.show()
