# In a new file (e.g., analyze.py)
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("requests.csv", names=["timestamp", "client_ip", "response_time"])

# Plot response times
plt.figure()
df["response_time"].plot.hist(bins=20)
plt.title("Response Time Distribution")
plt.savefig("response_times.png")
