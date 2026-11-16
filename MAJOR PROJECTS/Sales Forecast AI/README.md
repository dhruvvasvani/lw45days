# Sales Forecast AI

A Streamlit dashboard for exploring daily sales data, evaluating a Holt-Winters
forecast, and checking whether current stock covers the selected forecast period.

## Run locally

1. Open a terminal in this project folder.
2. (Recommended) Create and activate a virtual environment.
3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Start the dashboard:

   ```powershell
   streamlit run app.py
   ```

Streamlit opens the local dashboard in your browser. Select **Try demo data** to
explore it immediately, or choose **Upload a CSV** to use your own data.

## Publish the app

1. Push this project to a GitHub repository. Include `app.py`, the `backend/`
   folder, and `requirements.txt`.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), choose **Create
   app**, select the GitHub repository and branch, and set the app file path to
   `app.py`.
3. Deploy. The app installs its dependencies from `requirements.txt`.

Uploaded CSV data is processed in memory and is not included in the repository.

## CSV format

The uploaded CSV needs two columns:

| Column | Description |
| --- | --- |
| Date | A date parsable by pandas |
| Demand | A non-negative numeric quantity to forecast (sales, units, orders, riders, etc.) |

The dashboard detects common names such as `Date`, `Order Date`, `dteday`,
`Sales`, `Quantity`, `Units Sold`, `Revenue`, and `cnt`. If your headers use
different names, select the date and demand columns in the sidebar. Extra CSV
columns are allowed and ignored. The **Download CSV template** button provides
a ready-to-edit example with the required columns.

Rows with the same date are summed. Missing dates between the first and last
date are treated as zero-demand days and reported in the dashboard; verify that
this assumption is appropriate for your dataset. Upload daily records.

## What the dashboard reports

- Holt-Winters additive trend and seasonality forecast.
- Chronological holdout MAE and RMSE, rather than illustrative hardcoded metrics.
- Actual-vs-predicted validation, demand forecast, and trend/seasonal/residual charts.
- Optional inventory coverage analysis using the stock quantity entered in the sidebar.
- A downloadable CSV containing daily forecast, cumulative demand, projected stock,
  and inventory status.

The model expects daily data and at least three complete seasonal cycles. Its
accuracy metrics describe the historical holdout only and do not guarantee future
forecast accuracy.
