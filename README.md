# oopsAnddecorators


APIClient ek reusable OOP class hai jo async HTTP requests handle karta hai safe context manager ke saath.

Decorators (log_calls, timed, retry_async) har call ka log, execution time aur retry logic automatic add karte hain.

fetch_demo do alag base URLs se ek saath 5 endpoints call karta hai, async ke kaaran total time fastest call ke barabar hota hai.

async with ensure karta hai ki HTTP client open + close proper ho, warna _client not initialized error aata hai.

Output me tumhe logs + timings + summary milta hai — perfect demo of clean, modern Python async coding. 🚀
