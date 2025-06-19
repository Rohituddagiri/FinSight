from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from sec_edgar_api import EdgarClient
import httpx
import json
import os
import asyncio
import requests
import pandas as pd


mcp = FastMCP("sec-edgar-server")

load_dotenv()

USER_AGENT = "sec-edgar-app/1.0"


async def load_company_concepts_data(cik: str, taxonomy: str, tag: str) -> pd.DataFrame | None:
    edgar = EdgarClient(user_agent="uddagirirohit@gmail.com")
    
    company_concepts = edgar.get_company_concept(cik=cik, taxonomy=taxonomy, tag=tag)
    unit_key = list(company_concepts['units'].keys())[0]
    unit_data = company_concepts['units'][unit_key]
    unit_df = pd.DataFrame(unit_data)
    unit_df['filed'] = pd.to_datetime(unit_df['filed'], errors='coerce')
    unit_df['start'] = pd.to_datetime(unit_df['start'], errors='coerce')
    unit_df['end'] = pd.to_datetime(unit_df['end'], errors='coerce')
    unit_df = unit_df.dropna(subset=['filed'])
    unit_df.rename(columns={'val':unit_key}, inplace=True)
    
    unit_df['fy'] = unit_df['fy'].astype(pd.Int64Dtype())
    
    def infer_frame_from_start_end(row):
        if pd.notna(row['frame']):
            return row['frame']
        
        if pd.notna(row['start']) and pd.notna(row['end']):
            start_date = row['start']
            end_date = row['end']
            diff_days = (end_date-start_date).days
            if 350 <= diff_days <= 380:
                return f"CY{start_date.year}"
            elif (70 <= diff_days <= 110) & (row['fp'] in ['Q1','Q2','Q3','Q4']) :
                return f"CY{start_date.year}{row['fp']}"
        return None

    unit_df['frame'] = unit_df.apply(infer_frame_from_start_end, axis=1)
    unit_df = unit_df.dropna(subset=['frame'])
    
    return unit_df


async def load_company_facts_details(cik: str) -> pd.DataFrame | None:
    edgar = EdgarClient(user_agent="uddagirirohit@gmail.com")
    company_facts = edgar.get_company_facts(cik=cik)
    fact_rows = []

    for taxonomy, facts in company_facts['facts'].items():
        for fact_name, details in facts.items():
            label = details.get('label','')
            description = details.get('description','')
            fact_rows.append({
                'taxonomy': taxonomy,
                'fact_name': fact_name,
                'label': label,
                'description':description
                })
    fact_df = pd.DataFrame(fact_rows)
    fact_df = fact_df.dropna(subset=['label'])
    return fact_df

@mcp.tool()
async def get_company_cik_number(company_name: str):
    """
    Search the Company Tickers Exchange data to get
    cik number, ticker, title and exchange for the input company name.
    Args:
        company_name (str): The name of the Company to lookup for (e.g. "Apple")
        
    Returns:
        A dictionary with cik, tiker, title and exchange information
    """
    headers = {"User-Agent" : "uddagirirohit@gmail.com"}
    cik_lkp_data = requests.get('https://www.sec.gov/files/company_tickers_exchange.json', headers = headers)
    cik_df = pd.DataFrame.from_dict(cik_lkp_data.json()['data'])
    cik_df.columns = cik_lkp_data.json()['fields']
    result_dict = cik_df[cik_df['name'].str.contains(company_name, case=False)].iloc[0].to_dict()
    return result_dict


@mcp.tool()
async def get_company_facts_information(cik: str, keyword: str):
    """
    Retrieve relevant facts information available which includes
    taxonomy, fact name, lable and description details for the input 
    cik number and the keyword to filter relevant fact names.
    Args:
        cik (str): The cik number for a company (e.g. "0001717115")
        keyword (str): The lable name to search facts for (e.g. "amount", "equity","Income Tax")
    Returns:
        A dictionary of facts information that includes
        taxonomy of the fact, fact name, fact label, fact description
    """
    company_facts = await load_company_facts_details(cik=cik)
    
    relevant_company_facts = company_facts[company_facts.label.str.contains(keyword, case=False)]
    
    res = relevant_company_facts.to_dict(orient='records')
    
    return res

@mcp.tool()
async def get_available_frames_in_fiscial_year(cik: str, taxonomy: str, fact: str, fy:str):
    """
    Filters fact entries which contains the facts for each units on measure that the company has 
    chosen to disclose by fisical year and returns the frames that are filed for that fisical year.
    
    Args:
        cik (str): The cik number for a company (e.g. "0001717115")
        taxonomy (str): The taxonomy to which the fact belongs to (e.g. "us-gaap", "dei")
        fact (str): The full name of the fact to look up for(e.g. "AccountsReceivableNetCurrent")
        fy (str): Fiscal year (e.g. "2025", "2024").

    Returns:
        A list of frames that the company disclosed in the fisical year.
    """
    try:
        unit_df = await load_company_concepts_data(cik=cik,taxonomy=taxonomy,tag=fact)
        fy_df = unit_df[(unit_df['fy'] == int(fy))]
        
        results = list(fy_df['frame'].unique())
        return results if results else []
    except Exception as e:
        return f"Unable to Retrieve Data, {e}"


@mcp.tool()
async def get_data_for_frame(cik: str, taxonomy: str, fact: str, frame:str):
    """
    Filters fact entries which contains the facts for each units on measure that the company has 
    chosen to disclose and returns the most recent data available for the frame in a dictionary format.
    
    Args:
        cik (str): The cik number for a company (e.g. "0001717115")
        taxonomy (str): The taxonomy to which the fact belongs to (e.g. "us-gaap", "dei")
        fact (str): The full name of the fact to look up for(e.g. "AccountsReceivableNetCurrent")
        frame (str): Frame to lookup for (e.g. "CY2024","CY2021Q1")

    Returns:
        A dictionary of data that contains units on measure, fisical year, fisical period, filed form, filed date and frame.
    """
    try:
        unit_df = await load_company_concepts_data(cik=cik,taxonomy=taxonomy,tag=fact)
        
        frame_df = unit_df[unit_df['frame']==frame].sort_values(by='filed',ascending=False)
        results = frame_df.iloc[0,[2,4,5,6,7,8]].to_dict()
        
        return results if results else {}
    except Exception as e:
        return f"Unable to Retrieve Data, {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")