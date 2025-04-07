import requests
import json
import time
import sys

# Replace with your actual Render URL after deployment
SCRAPER_URL = "https://facebook-scraper-api.onrender.com"

def scrape_facebook_post(post_url):
    """
    Sends a request to the deployed scraper API and returns the scraped data
    """
    # Check if the service is online (important for Render free tier which spins down after inactivity)
    try:
        health_check = requests.get(f"{SCRAPER_URL}/")
        if health_check.status_code != 200:
            print(f"Service appears to be offline or starting up. Status: {health_check.status_code}")
            print("If using free tier, the service may take 1-2 minutes to start...")
    except requests.exceptions.ConnectionError:
        print("Cannot connect to the service. It may be spinning up if using Render free tier.")
        print("Please wait 1-2 minutes and try again.")
        return None

    # Prepare the request data
    payload = {"post_url": post_url}
    
    print(f"Sending request to scrape post: {post_url}")
    print("This may take some time depending on the post size and number of comments...")
    
    try:
        # Send the request to the API
        response = requests.post(
            f"{SCRAPER_URL}/scrape-facebook-post",
            json=payload,
            timeout=300  # 5-minute timeout for long-running scrapes
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
            
    except requests.exceptions.Timeout:
        print("Request timed out. The scraping operation may be taking too long.")
        print("Consider scraping a post with fewer comments or upgrading your Render plan.")
        return None
    except requests.exceptions.ConnectionError:
        print("Connection error. The service may be overloaded or experiencing issues.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None

def display_results(data):
    """
    Formats and displays the scraped data in a readable format
    """
    if not data:
        return
    
    print("\n" + "="*80)
    print(f"POST CONTENT:\n{data['post']['content']}")
    print("="*80)
    
    print(f"\nTotal Comments: {data['metadata']['total_comments']}")
    print(f"Scraped at: {data['metadata']['scraped_at']}")
    
    print("\nCOMMENTS:")
    for i, comment in enumerate(data['comments'], 1):
        print(f"\n{i}. Author: {comment['author']}")
        print(f"   {comment['comment']}")
    
    print("\n" + "="*80)

def save_to_json(data, filename="scraped_post.json"):
    """
    Saves the scraped data to a JSON file
    """
    if not data:
        return
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nData saved to {filename}")

def main():
    # Allow command-line input of the post URL
    if len(sys.argv) > 1:
        post_url = sys.argv[1]
    else:
        post_url = input("Enter the Facebook post URL to scrape: ")
    
    # Start timer to measure performance
    start_time = time.time()
    
    # Call the API
    result = scrape_facebook_post(post_url)
    
    # Display performance metric
    elapsed_time = time.time() - start_time
    print(f"\nScraping completed in {elapsed_time:.2f} seconds")
    
    # Display and save results
    if result:
        display_results(result)
        save_to_json(result)

if __name__ == "__main__":
    main()