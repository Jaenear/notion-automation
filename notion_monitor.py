name: Monitor Notion Database
on:
  schedule:
    - cron: "*/6 * * * *"  # 매 6분마다 실행
  workflow_dispatch:
jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.x
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Load last check time
        run: |
          if [ -f last_check_time.txt ]; then
            echo "Last check time file exists"
            cat last_check_time.txt
          else
            echo "Last check time file does not exist. Creating a new one."
            echo "2021-01-01T00:00:00.000Z" > last_check_time.txt
      
      - name: Run Notion monitor script
        env:
          NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
          DATABASE_ID: ${{ secrets.DATABASE_ID }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: python notion_monitor.py
      
      - name: Save last check time
        if: always()
        run: cat last_check_time.txt >> $GITHUB_ENV
