import requests
from bs4 import BeautifulSoup

# Headers to mimic a real browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def fetch_post_data(url,num_of_comments):
    """Scrapes a Reddit post from old.reddit.com and extracts its content and top 2 comments (text only)."""

    # Convert 'www.reddit.com' to 'old.reddit.com'
    url = url.replace("www.reddit.com", "old.reddit.com")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raises an error for 4xx/5xx HTTP responses
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the post: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Locate the main post inside the siteTable
    site_table = soup.find("div", id="siteTable")
    if not site_table:
        print("Failed to locate the post content.")
        return {"content": "Post content not available", "comments": []}

    # Extracting the main post content
    post_element = site_table.select_one(".usertext-body .md")
    post_content = post_element.get_text(strip=True) if post_element else None

    # If no text content is found, use the post title as a fallback
    title_element = site_table.select_one(".title a")
    post_title = (
        title_element.get_text(strip=True) if title_element else "Unknown Title"
    )

    # Use title if content is empty
    post_content = (
        post_content if post_content else f"[No post text] Title: {post_title}"
    )

    # Extracting top 2 comments
    comments = []
    comment_elements = soup.select(".comment")

    for comment in comment_elements[:num_of_comments]:  # Get only top 2 comments
        text_element = comment.select_one(".md")

        comment_data = {
            "text": (
                text_element.get_text(strip=True)
                if text_element
                else "Comment not available"
            ),
        }

        comments.append(comment_data)

    # If no comments are found
    if not comments:
        comments.append({"text": "No comments available"})

    # Creating structured result
    result = {"content": post_content, "comments": comments}

    return result


# Example usage:
reddit_link = "https://www.reddit.com/r/golang/comments/1hv9apb/what_are_the_reasons_for_not_picking_go_templates/"
data = fetch_post_data(reddit_link,3)

print(data)
