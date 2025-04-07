from fastapi import FastAPI, HTTPException, Body
from typing import Dict
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import uvicorn
from pydantic import BaseModel, Field
import os

app = FastAPI(
    title="Facebook Post Scraper API",
    description="API to scrape Facebook posts and comments using stored credentials",
    version="1.0.0"
)

# Hardcoded Facebook credentials as secrets
# For better security, you can use environment variables instead
FB_CREDENTIALS = {
    "email": os.environ.get("FB_EMAIL", "saadmomin5555@gmail.com"),
    "password": os.environ.get("FB_PASSWORD", "Saad@2903")
}

# Input model for better API documentation
class PostRequest(BaseModel):
    post_url: str = Field(..., description="URL of the Facebook post to scrape")

@app.get("/", tags=["Health Check"])
async def root():
    """Health check endpoint"""
    return {"status": "online", "service": "Facebook Post Scraper API"}

@app.post("/scrape-facebook-post", 
         description="Scrape a Facebook post and its comments using stored credentials")
async def get_facebook_comments(request: PostRequest):
    # Get the post URL from the request
    post_url = request.post_url
    
    # Use the hardcoded credentials
    email = FB_CREDENTIALS["email"]
    password = FB_CREDENTIALS["password"]

    # Start the browser session
    async with async_playwright() as p:
        # Use headless mode but with additional configurations to avoid detection
        browser = await p.chromium.launch(
            headless=True,  
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                # Optimize for Render's resources
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-accelerated-2d-canvas',
                '--disable-accelerated-jpeg-decoding',
                '--disable-accelerated-mjpeg-decode',
                '--disable-accelerated-video-decode',
                # Needed to avoid captcha 
                '--proxy-server="direct://"',
                '--proxy-bypass-list=*',
                # Fingerprinting prevention
                '--disable-blink-features=AutomationControlled',
                # Memory optimization
                '--js-flags="--max-old-space-size=460"',
                # Original anti-bot args
                '--disable-infobars',
                '--disable-background-networking',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-breakpad',
                '--disable-component-extensions-with-background-pages',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
                '--enable-features=NetworkService,NetworkServiceInProcess',
                '--force-color-profile=srgb',
                '--metrics-recording-only',
                '--mute-audio',
            ]
        )
        
        # Create a context with more realistic browser parameters
        context = await browser.new_context(
            viewport={"width": 1366, "height": 768},  # Smaller viewport to save memory
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            is_mobile=False,
            has_touch=False,
            locale='en-US',
            timezone_id='America/New_York',
            color_scheme='light',
            java_script_enabled=True,
            bypass_csp=True,
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1'
            }
        )
        
        # Add stealth.min.js to avoid detection
        await context.add_init_script("""
        const newProto = navigator.__proto__;
        delete newProto.webdriver;
        navigator.__proto__ = newProto;
        
        // Store the existing descriptor
        const originalQuery = window.navigator.permissions.query;
        
        // Redefine the method
        window.navigator.permissions.query = (parameters) => {
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return originalQuery(parameters);
        };
        
        // Plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                return [
                    {
                        0: {
                            type: 'application/x-google-chrome-pdf',
                            suffixes: 'pdf',
                            description: 'Portable Document Format',
                            enabledPlugin: Plugin,
                            __proto__: MimeType
                        },
                        name: 'Chrome PDF Plugin',
                        filename: 'internal-pdf-viewer',
                        description: 'Portable Document Format',
                        __proto__: Plugin
                    },
                    {
                        0: {
                            type: 'application/pdf',
                            suffixes: 'pdf',
                            description: '',
                            enabledPlugin: Plugin,
                            __proto__: MimeType
                        },
                        name: 'Chrome PDF Viewer',
                        filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                        description: '',
                        __proto__: Plugin
                    },
                    {
                        0: {
                            type: 'application/x-nacl',
                            suffixes: '',
                            description: 'Native Client Executable',
                            enabledPlugin: Plugin,
                            __proto__: MimeType
                        },
                        1: {
                            type: 'application/x-pnacl',
                            suffixes: '',
                            description: 'Portable Native Client Executable',
                            enabledPlugin: Plugin,
                            __proto__: MimeType
                        },
                        name: 'Native Client',
                        filename: 'internal-nacl-plugin',
                        description: '',
                        __proto__: Plugin
                    }
                ]
            }
        });
        
        // Languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
        
        // Add canvas fingerprint
        const getParameter = WebGLRenderingContext.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.apply(this, [parameter]);
        };
        """)
        
        # Enable JavaScript console logging
        context.on('console', lambda msg: print(f'BROWSER LOG: {msg.text}'))
        
        page = await context.new_page()

        # Add script to remove navigator.webdriver flag
        await page.add_init_script('''() => {
            // Overwrite the 'webdriver' property to undefined
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Overwrite the chrome driver related properties
            window.navigator.chrome = { runtime: {} };
            
            // Overwrite the permissions API
            window.navigator.permissions = {
                query: () => Promise.resolve({ state: 'granted' })
            };
            
            // Add missing plugins that a normal browser would have
            const originalPlugins = navigator.plugins;
            const pluginsData = [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                { name: 'Native Client', filename: 'internal-nacl-plugin' }
            ];
            
            // Define a new plugins property
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = { 
                        ...originalPlugins,
                        length: pluginsData.length 
                    };
                    
                    // Add the missing plugins
                    pluginsData.forEach((plugin, i) => {
                        plugins[i] = plugin;
                    });
                    
                    return plugins;
                }
            });
            
            // Fake the language property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Fake the platform to match a Mac
            Object.defineProperty(navigator, 'platform', {
                get: () => 'MacIntel'
            });
            
            // Add a fake notification API
            if (window.Notification) {
                window.Notification.permission = 'default';
            }
        }''')

        try:
            # Step 1: Login to Facebook
            await page.goto('https://www.facebook.com/', timeout=60000)
            
            # Wait for page to fully load
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)  # Additional delay
            
            # Accept cookies if present
            try:
                cookie_button = await page.query_selector('button[data-cookiebanner="accept_button"]')
                if cookie_button:
                    await cookie_button.click()
                    await asyncio.sleep(1)
            except Exception:
                print('No cookie banner found')

            # Login
            await page.fill('#email', email)
            await page.fill('#pass', password)
            
            # Click login button
            await page.click('button[name="login"]')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            # Check for CAPTCHA or checkpoint
            if 'checkpoint' in page.url:
                print("Detected checkpoint/CAPTCHA page")
                # Wait for user to manually solve CAPTCHA - longer timeout
                await asyncio.sleep(30)  # Give 30 seconds for manual CAPTCHA solving
                
                # Wait for navigation after CAPTCHA is solved
                await page.wait_for_load_state('networkidle')
                
                # Check if we're still on checkpoint page
                if 'checkpoint' in page.url:
                    raise HTTPException(status_code=401, detail='CAPTCHA/checkpoint not solved in time. Please try again.')

            # Check login success
            if 'login' in page.url:
                raise HTTPException(status_code=401, detail='Login failed - Please check credentials')

            # Step 2: Scrape the post and comments
            print(f"Navigating to post URL: {post_url}")
            await page.goto(post_url, timeout=60000)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(5)  # Wait longer for all elements to load

            # Get post content
            post_data = await page.evaluate('''() => {
                // Try to get the post description directly from where Facebook actually stores it
                const getPostDescription = () => {
                    // First approach: Get the full text content from the post container
                    const postContainer = document.querySelector('.xjkvuk6, .xuyqlj2');
                    if (postContainer) {
                        // Get all text content divs in the post container
                        const textDivs = Array.from(postContainer.querySelectorAll('div[dir="auto"]'))
                            .map(el => el.textContent.trim())
                            .filter(text => text.length > 10 && !text.includes('See more') && !text.includes('See less'));
                        
                        // Get the full post content by joining all text segments (this gets the complete text even if split across divisions)
                        if (textDivs.length > 0) {
                            return textDivs.join(' ');
                        }
                    }
                    
                    // Second approach: Look for specific post wrapper divs by their class names
                    const wrapperSelectors = [
                        'div.x11i5rnm.xat24cr.x1mh8g0r.x1vvkbs',
                        'div.x78zum5.xdt5ytf.x4cne27.xifccgj',
                        'div.xzueoph.x1k70j0n',
                        'div.x1n2onr6'
                    ];
                    
                    for (const selector of wrapperSelectors) {
                        const wrappers = document.querySelectorAll(selector);
                        for (const wrapper of wrappers) {
                            const texts = Array.from(wrapper.querySelectorAll('div[dir="auto"], span[dir="auto"]'))
                                .map(el => el.textContent.trim())
                                .filter(text => 
                                    text.length > 30 && 
                                    !text.includes('See more') && 
                                    !text.includes('See less') &&
                                    !text.includes('#') // Avoid hashtag sections
                                );
                            
                            if (texts.length > 0) {
                                // Sort by length and get the longest text
                                return texts.sort((a, b) => b.length - a.length)[0];
                            }
                        }
                    }
                    
                    // Third approach: look for any lengthy content in the first article element (likely the post itself)
                    const firstArticle = document.querySelector('div[role="article"]');
                    if (firstArticle) {
                        const articleTexts = Array.from(firstArticle.querySelectorAll('div[dir="auto"]'))
                            .map(el => el.textContent.trim())
                            .filter(text => 
                                text.length > 40 && 
                                !text.includes('See more') && 
                                !text.includes('See less')
                            );
                        
                        if (articleTexts.length > 0) {
                            // Sort by length to get the most substantial content
                            return articleTexts.sort((a, b) => b.length - a.length)[0];
                        }
                    }
                    
                    // Final fallback: any meaningful content on the page
                    const allTextElements = Array.from(document.querySelectorAll('div[dir="auto"]'));
                    const allTexts = allTextElements
                    .map(el => el.textContent.trim())
                        .filter(text => text.length > 50);
                        
                    if (allTexts.length > 0) {
                        return allTexts.sort((a, b) => b.length - a.length)[0];
                    }
                    
                    return '';
                };

                return {
                    post_content: getPostDescription(),
                    post_url: window.location.href
                };
            }''')

            # Step 3: Expand all comments using multiple strategies
            max_attempts = 15  # Increased from 10 to give more time for comments to load
            attempts = 0
            total_clicks = 0
            last_comment_count = 0

            # First, add a longer initial wait to ensure the page loads completely
            await asyncio.sleep(8)  # Increased initial wait time
            await page.wait_for_load_state('networkidle')

            # More aggressive scroll to ensure all content is loaded
            await page.evaluate('''() => {
                // Perform multiple scrolls to ensure content is loaded
                const scrollDown = () => {
                    window.scrollTo(0, document.body.scrollHeight);
                    return new Promise(resolve => setTimeout(resolve, 500));
                };
                
                return (async () => {
                    for (let i = 0; i < 5; i++) {
                        await scrollDown();
                    }
                    return true;
                })();
            }''')
            await asyncio.sleep(5)  # Wait longer after scrolling

            # Try to directly find the comments section and force it to be visible
            await page.evaluate('''() => {
                // Try to identify and force visibility of comments sections
                const possibleCommentSections = [
                    'div[aria-label="Comments"]',
                    'div.x1j85h84',
                    'div.x4k7w5x',
                    'div.x1pi30zi',
                    'div[data-pagelet="Comments"]',
                    'div.xsag5q8'
                ];
                
                for (const selector of possibleCommentSections) {
                    const section = document.querySelector(selector);
                    if (section) {
                        // Force visibility
                        section.style.display = 'block';
                        section.style.visibility = 'visible';
                        section.scrollIntoView({behavior: 'smooth', block: 'center'});
                        console.log("Found and made visible comment section with selector:", selector);
                    }
                }
                
                // Also try to click any "View comments" or "View more comments" buttons
                const commentButtons = Array.from(document.querySelectorAll('div[role="button"]'))
                    .filter(el => {
                        const text = el.textContent.toLowerCase();
                        return text.includes('view') && (text.includes('comment') || text.includes('reply'));
                    });
                
                if (commentButtons.length > 0) {
                    console.log("Found comment buttons:", commentButtons.length);
                    commentButtons.forEach(button => {
                        try {
                            button.click();
                            console.log("Clicked a comment button");
                        } catch (e) {
                            console.error("Error clicking button:", e);
                        }
                    });
                }
            })''')
            await asyncio.sleep(5)  # Wait after trying to force comment visibility

            while attempts < max_attempts:
                # Get current comment count to check if we're making progress
                current_comment_count = await page.evaluate('''() => {
                    return document.querySelectorAll('div[role="article"]').length;
                }''')
                
                print(f"Current comment count: {current_comment_count}")
                
                if current_comment_count == last_comment_count and attempts > 3:  # Reduced from 5 to save resources
                    print("No new comments loaded after several attempts, stopping")
                    break
                    
                last_comment_count = current_comment_count
                
                # Add improved comment detection that tries multiple selectors
                if current_comment_count == 0 and attempts >= 3:
                    print("Still no comments detected, trying alternative selectors...")
                    alternative_count = await page.evaluate('''() => {
                        // Try different selectors for comments
                        const selectors = [
                            'div.x1lliihq',
                            'div.x1n2onr6',
                            'div.x78zum5',
                            'div.xzueoph',
                            'div.xms4yrp',
                            'div.x1r8uery',
                            'div[data-testid="UFI2CommentsList/root"]',
                            'ul[data-testid="UFI2CommentsList/root"]',
                            'div.x1jx94hy',
                            'form ~ div > div',  // Comments often appear after the comment form
                            'div.x168nmei',
                            'div.x13lgxp2'
                        ];
                        
                        for (const selector of selectors) {
                            const elements = document.querySelectorAll(selector);
                            const possibleComments = Array.from(elements).filter(el => {
                                // Look for elements that have typical comment characteristics
                                const hasText = el.textContent.length > 20;
                                const hasAuthor = el.querySelector('a[role="link"]') !== null;
                                const isVisible = el.offsetWidth > 0 && el.offsetHeight > 0;
                                const notPost = !el.textContent.includes("Share") && !el.textContent.includes("Like");
                                
                                return hasText && isVisible && (hasAuthor || notPost);
                            });
                            
                            if (possibleComments.length > 0) {
                                console.log("Found potential comments using selector:", selector, possibleComments.length);
                                return possibleComments.length;
                            }
                        }
                        
                        // If still no comments, check for specific comment patterns
                        const allDivs = document.querySelectorAll('div');
                        const textContainers = Array.from(allDivs).filter(div => {
                            const text = div.textContent.trim();
                            return text.length > 30 && 
                                  !text.includes("See more") && 
                                  !text.includes("View more comments") &&
                                  div.querySelectorAll('a, span').length > 0;
                        });
                        
                        if (textContainers.length > 0) {
                            console.log("Found text containers that might be comments:", textContainers.length);
                            return textContainers.length;
                        }
                        
                        return 0;
                    }''');
                    
                    if alternative_count > 0:
                        print(f"Found {alternative_count} potential comments using alternative selectors")
                        current_comment_count = alternative_count
                
                # More efficient scrolling strategy for headless mode
                await page.evaluate('''() => {
                    // Scroll down once with small pause
                    window.scrollTo(0, document.body.scrollHeight);
                    return true;
                }''')
                await asyncio.sleep(2)

                # First strategy: Use standard querySelector methods with text content checking
                click_happened = await page.evaluate('''() => {
                    // Function to simulate human-like clicking
                    const humanClick = (element) => {
                        element.click();
                        return true;
                    };
                    
                    // Try to find spans with the specific text content
                    const allSpans = Array.from(document.querySelectorAll('span'));
                    
                    // Look for spans with the exact class from the example
                    const targetSpans = allSpans.filter(span => {
                        const hasClass = span.className.includes('x193iq5w');
                        const hasText = span.textContent.includes('View more comments') || 
                                       span.textContent.includes('Previous comments');
                        return hasClass && hasText;
                    });
                    
                    // If we found target spans with the right class, try to click their parent buttons
                    if (targetSpans.length > 0) {
                        for (const span of targetSpans) {
                            const clickable = span.closest('div[role="button"]');
                            if (clickable) {
                                console.log("Found clickable with x193iq5w class");
                                clickable.scrollIntoView({behavior: "auto", block: "center"});
                                return humanClick(clickable);
                            }
                        }
                    }
                    
                    // Fallback: try all spans with the right text
                    for (const span of allSpans) {
                        if (span.textContent.includes('View more comments') || 
                            span.textContent.includes('Previous comments')) {
                            const clickable = span.closest('div[role="button"]');
                            if (clickable) {
                                console.log("Found clickable via text content search");
                                clickable.scrollIntoView({behavior: "auto", block: "center"});
                                return humanClick(clickable);
                            }
                        }
                    }
                    
                    // Try direct role buttons that contain the text
                    const buttons = Array.from(document.querySelectorAll('div[role="button"]'));
                    for (const button of buttons) {
                        if (button.textContent.includes('View more comments') || 
                            button.textContent.includes('Previous comments')) {
                            console.log("Found direct button");
                            button.scrollIntoView({behavior: "auto", block: "center"});
                            return humanClick(button);
                        }
                    }
                    
                    return false;
                }''')

                if click_happened:
                    print("Clicked on 'View more comments' button")
                    total_clicks += 1
                    await asyncio.sleep(3)  # Reduced from 4
                    await page.wait_for_load_state('networkidle')
                else:
                    print("No more 'View more comments' buttons found")
                    
                    if total_clicks == 0 or attempts > 5:  # Reduced from 10
                        # If we haven't clicked anything or tried many times, break the loop
                        break
                
                attempts += 1
                
                # Add a comment count limit to avoid resource exhaustion
                if current_comment_count > 50:  # Limit to 50 comments to save resources
                    print("Reached comment limit to save resources")
                    break
            
            print(f"Made {total_clicks} clicks to expand comments")
            
            # Step 4: Scrape the comments - use a more robust approach
            comments = await page.evaluate('''() => {
                const comments = [];
                
                // Try multiple selectors for comment elements
                const commentSelectors = [
                    'div[role="article"]',
                    'div.x1lliihq',
                    'div.x1n2onr6 > div.x78zum5',
                    'div.xzueoph',
                    'div.x168nmei',
                    'div.x13lgxp2',
                    'div[data-testid="UFI2Comment/root_depth_0"]',
                    'div.x1r8uery',
                    'div.x1jx94hy'
                ];
                
                // Try each selector
                let commentElements = [];
                for (const selector of commentSelectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 1) {  // More than 1 to skip the post itself
                        console.log(`Found ${elements.length} elements with selector: ${selector}`);
                        commentElements = Array.from(elements);
                        // Skip the first element only if we have multiple, as it might be the post
                        if (elements.length > 1) {
                            commentElements = commentElements.slice(1);
                        }
                        break;
                    }
                }
                
                // If still no comments via selectors, try a more general approach
                if (commentElements.length === 0) {
                    console.log("No comments found via selectors, trying general approach");
                    
                    // Find potential comment containers - look for text blocks in the page
                    const allDivs = document.querySelectorAll('div');
                    commentElements = Array.from(allDivs).filter(div => {
                        // Skip extremely small or empty divs
                        if (div.offsetWidth < 100 || div.offsetHeight < 30 || div.textContent.trim().length < 20) {
                            return false;
                        }
                        
                        // Look for divs that might contain comments (has text, maybe links, deeper in the page)
                        const hasText = div.textContent.trim().length > 30;
                        const notHeader = !div.textContent.includes("Comments") && !div.textContent.includes("Most Relevant");
                        const notPost = !div.textContent.includes("Share") || div.querySelectorAll('button').length < 3;
                        const mightBeComment = div.querySelectorAll('a').length > 0 || div.querySelectorAll('span').length > 2;
                        
                        return hasText && notHeader && notPost && mightBeComment;
                    });
                }
                
                console.log("Total comment elements found for processing:", commentElements.length);
                
                // Process found comment elements
                // Limit to 100 comments to save resources
                const limitedComments = commentElements.slice(0, 100);
                
                limitedComments.forEach((comment, index) => {
                    try {
                        // Extract the comment content
                        // First try specific dir="auto" elements which typically contain the main text
                        let content = '';
                        const contentElements = comment.querySelectorAll('div[dir="auto"], span[dir="auto"]');
                        
                        if (contentElements.length > 0) {
                            // Take the longest text content as the comment
                            contentElements.forEach(el => {
                                const text = el.textContent.trim();
                                if (text && 
                                    text.length > content.length && 
                                    !text.includes("See more") && 
                                    !text.includes("Like") && 
                                    !text.includes("Reply")) {
                                    content = text;
                                }
                            });
                        }
                        
                        // If no content found with dir="auto" elements, try any text content
                        if (!content || content.length < 15) {
                            // Get all text nodes in the comment
                            const walker = document.createTreeWalker(comment, NodeFilter.SHOW_TEXT);
                            let texts = [];
                            let node;
                            while (node = walker.nextNode()) {
                                const text = node.textContent.trim();
                                if (text && text.length > 10) {
                                    texts.push(text);
                                }
                            }
                            
                            // Find the longest text section that's not a button or UI element
                            if (texts.length > 0) {
                                texts.sort((a, b) => b.length - a.length);
                                for (const text of texts) {
                                    if (!text.includes("Like") && 
                                        !text.includes("Reply") && 
                                        !text.includes("See more") &&
                                        text.length > 15) {
                                        content = text;
                                        break;
                                    }
                                }
                            }
                        }
                        
                        // Extract the author name using various selectors to catch different FB layouts
                        let author = '';
                        
                        // First try: Look for the author name in specific class patterns
                        const authorElements = [
                            // Common FB patterns for author names
                            ...comment.querySelectorAll('strong, h3, h4, a[role="link"] span'),
                            // Mobile FB pattern - span with author class
                            ...comment.querySelectorAll('span.f20, span.x1heor9g, span.xt0psk2'),
                            // Profile links often contain the author name
                            ...comment.querySelectorAll('a[href*="/profile.php"], a[href*="facebook.com/"]')
                        ];
                        
                        // Try to extract author from the found elements
                        for (const el of authorElements) {
                            const name = el.textContent.trim();
                            if (name && name.length > 0 && name.length < 50 &&
                                !name.includes("Like") && 
                                !name.includes("Reply") &&
                                !name.includes("See more")) {
                                author = name;
                                break;
                            }
                        }
                        
                        // If no author found with specific selectors, try more general approach
                        if (!author) {
                            // Try to find author by position (usually at the beginning of the comment)
                            const allTexts = Array.from(comment.querySelectorAll('*'))
                                .map(el => el.textContent.trim())
                                .filter(text => text.length > 0 && text.length < 40);
                            
                            if (allTexts.length > 0) {
                                author = allTexts[0]; // First text is often the author
                            }
                        }
                        
                        if (content && content.length > 15) {
                            comments.push({
                                'comment': content,
                                'author': author || 'Unknown User',
                                'index': index
                            });
                        }
                    } catch (e) {
                        console.error('Error processing comment:', e);
                    }
                });

                return comments;
            }''')

            # Skip screenshot on Render to save disk space and memory
            # await page.screenshot(path='facebook_post_screenshot.png')

            formatted_data = {
                'post': {
                    'content': post_data['post_content'],
                    'url': post_data['post_url']
                },
                'comments': comments,
                'metadata': {
                    'total_comments': len(comments),
                    'scraped_at': datetime.now().isoformat(),
                    'clicks_to_expand': total_clicks
                }
            }

            # Close the browser
            await browser.close()

            return formatted_data

        except Exception as e:
            await browser.close()
            raise HTTPException(status_code=500, detail=f"Error scraping post: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)