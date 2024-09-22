import streamlit as st
import pandas as pd
from selenium import webdriver
from lxml import html

# Function to scrape data from a given URL and table ID
def scrape_data(url, table_id, columns_to_drop):
    driver = webdriver.Chrome()
    driver.get(url)
    html_source = driver.page_source
    doc = html.fromstring(html_source)
    
    # Extract the table
    table = doc.xpath(f'//*[@id="{table_id}"]')
    
    if table:
        df = pd.read_html(html.tostring(table[0]), header=1)[0]
        df = df.drop(columns=columns_to_drop, errors='ignore')
        if 'Player' in df.columns:
            df = df[~df['Player'].str.contains("Player", na=False)]
        driver.quit()
        return df
    else:
        st.error(f"Table with id '{table_id}' not found.")
        driver.quit()
        return None

# Main function to run the app
def main():
    st.title('Premier League Stats Scraper')
    st.write('This app scrapes data from FBRef.com and displays it in a table.')
    
    # URLs and table configurations with columns to drop
    urls_and_ids = [
        ("https://fbref.com/en/comps/9/misc/Premier-League-Stats", "stats_misc", ['90s', '2CrdY', 'Crs', 'Int', 'PKwon', 'PKcon', 'OG', 'Recov', 'Won', 'Lost', 'Won%', 'Rk', 'Matches', 'Nation', 'Age', 'Born', 'Off']),
        ("https://fbref.com/en/comps/9/shooting/Premier-League-Stats", "stats_shooting", ['Rk', 'Squad', '90s', 'Matches', 'Nation', 'Pos', 'Age', 'Born', 'SoT%', 'G/SoT', 'G/Sh', 'np:G-xG', 'G-xG', 'npxG/Sh']),
        ("https://fbref.com/en/comps/9/stats/Premier-League-Stats", "stats_standard", ['Rk', 'Nation', 'Pos', 'Age', 'Born', 'Squad', '90s', 'Starts', 'Goals', 'Assists', 'PK', 'PKatt'])
    ]
    
    if st.button('Scrape Data'):
        dataframes = []
        for url, table_id, columns_to_drop in urls_and_ids:
            df = scrape_data(url, table_id, columns_to_drop)
            if df is not None:
                df['Source'] = table_id  # Add a source identifier column
                dataframes.append(df)
        
        if dataframes:
            # Separate the 'misc', 'shooting', and 'standard' stats
            misc_df = dataframes[0][dataframes[0]['Source'] == 'stats_misc'].drop(columns=['Source'])
            shooting_df = dataframes[1][dataframes[1]['Source'] == 'stats_shooting'].drop(columns=['Source'])
            standard_df = dataframes[2][dataframes[2]['Source'] == 'stats_standard'].drop(columns=['Source'])

            # Keep only 'Player', 'MP', and 'Min' from the standard stats
            standard_df = standard_df[['Player', 'MP', 'Min']]
            
            # Convert 'Min' column to numeric to ensure proper filtering/sorting
            standard_df['Min'] = pd.to_numeric(standard_df['Min'], errors='coerce')
            
            # Replace NaN values in 'Min' with 0 (or any other default value)
            standard_df['Min'].fillna(0, inplace=True)
            
            # Merge the misc, shooting, and standard dataframes on 'Player'
            combined_df = pd.merge(misc_df, shooting_df, on='Player', how='outer')
            combined_df = pd.merge(combined_df, standard_df, on='Player', how='outer')
            
            # Drop the index column and reset index
            combined_df = combined_df.reset_index(drop=True)
            
            # Move 'Player', 'MP', and 'Min' to the front
            cols = ['Player', 'MP', 'Min'] + [col for col in combined_df.columns if col not in ['Player', 'MP', 'Min']]
            combined_df = combined_df[cols]

            combined_df.rename(columns={'MP': 'Matches', 'CrdY': 'Yellows', 'CrdR': 'Reds', 'Fls': 'Fouls', 'Fld': 'Fouled', 'TklW': 'Tackles Won', 'Dist': 'Avg Dist Of Shot', 'Sh': 'Shots', 'PK': 'Pens Scored'}, inplace=True)
            
            # Display the filtered dataframe with horizontal scrolling
            st.dataframe(combined_df, height=600, use_container_width=True)
            
        else:
            st.warning('No data scraped.')
            
if __name__ == "__main__":
    main()