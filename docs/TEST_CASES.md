# SmartAssist Test Plan

The WeIntern handbook asks for at least 20 diverse user inputs. This project targets 30+.

| # | Test input | Expected behavior |
|---|---|---|
| 1 | hello | greeting |
| 2 | hey SmartAssist | greeting |
| 3 | goodbye | goodbye |
| 4 | thanks for helping | thanks |
| 5 | what can you do? | help |
| 6 | when are you open? | business_hours |
| 7 | can I reach a human? | contact_support |
| 8 | what are your plans? | pricing |
| 9 | how much is Pro? | pricing |
| 10 | I need a refund | refund |
| 11 | can I get my money back? | refund |
| 12 | do you take UPI? | payment_methods |
| 13 | can I pay by debit card? | payment_methods |
| 14 | where is my order? | order_status + ask for order ID |
| 15 | ORD10001 | continue previous order context |
| 16 | can I cancel it? | cancel_order using context |
| 17 | track ORD10002 | order_status |
| 18 | is ORD10004 delivered? | order_status |
| 19 | I want to cancel ORD10001 | cancel_order |
| 20 | the website is broken | technical_issue |
| 21 | I cannot login | technical_issue |
| 22 | what are your opening hours on Sunday? | business_hours |
| 23 | hello, can you help me with a refund? | refund / helpful response |
| 24 | tell me something unrelated to shopping | unknown fallback |
| 25 | write me a poem | unknown fallback |
| 26 | qwerty12345 | unknown fallback |
| 27 | (empty message) | frontend/backend validation error |
| 28 | very long message | input length validation |
| 29 | API key invalid | authentication error handling |
| 30 | rate limit reached | rate-limit fallback |
| 31 | what payment options do you have? | payment_methods |
| 32 | when will my package arrive? | order_status |
| 33 | I want my order stopped | cancel_order |
| 34 | thanks, that's all | goodbye / thanks |
| 35 | can someone help me? | help / contact_support based on context |
