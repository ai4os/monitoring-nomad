import json

from fastapi import FastAPI

from cluster_overview import get_cluster_overview_df



app = FastAPI(title="Cluster Overview API")

@app.get("/cluster-overview/json")
def get_cluster_overview_json():
    """
    Retrieves and exposes the cluster overview data directly as JSON.
    """
    # Call the logic directly
    df = get_cluster_overview_df()

    # df.to_json automatically handles NaNs and converts them to nulls for JSON
    return json.loads(df.to_json(orient="records"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
