import random
from typing import List, Dict, Any
from backend.models.product import Product, Review
from backend.database import get_db

# Mock templates for creating products
BRANDS_CATEGORIES = {
    "Smartphones": {
        "Apple": ["iPhone 17 Pro Max", "iPhone 17 Pro", "iPhone 17 Plus", "iPhone 17", "iPhone 16 Pro Max", "iPhone 16 Pro", "iPhone 16 Plus", "iPhone 16", "iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15 Plus", "iPhone 15", "iPhone 14 Pro Max", "iPhone 14 Pro", "iPhone 14 Plus", "iPhone 14", "iPhone 13 Pro Max", "iPhone 13 Pro", "iPhone 13", "iPhone SE (3rd Gen)"],
        "Samsung": ["Galaxy S26 Ultra", "Galaxy S26+", "Galaxy S26", "Galaxy S25 Ultra", "Galaxy S25+", "Galaxy S25", "Galaxy S24 Ultra", "Galaxy S24+", "Galaxy S24", "Galaxy S23 Ultra", "Galaxy S23 FE", "Galaxy Fold 6", "Galaxy Flip 6", "Galaxy A55 5G", "Galaxy A35 5G", "Galaxy M55 5G", "Galaxy F55 5G"],
        "OnePlus": ["OnePlus 14 Pro", "OnePlus 14", "OnePlus 13R", "OnePlus 13", "OnePlus 12R", "OnePlus 12", "OnePlus 11R", "OnePlus 11", "OnePlus Nord 4", "OnePlus Nord CE4", "OnePlus Nord CE4 Lite"],
        "Google": ["Pixel 10 Pro Fold", "Pixel 10 Pro XL", "Pixel 10 Pro", "Pixel 10", "Pixel 9 Pro XL", "Pixel 9 Pro", "Pixel 9", "Pixel 8a", "Pixel 8 Pro", "Pixel 8", "Pixel 7a", "Pixel 7 Pro", "Pixel 7"],
        "Xiaomi": ["Xiaomi 14 Ultra", "Xiaomi 14", "Xiaomi 13 Pro", "Redmi Note 13 Pro+", "Redmi Note 13 Pro", "Redmi Note 13", "Redmi 13C", "Poco F6 Pro", "Poco F6", "Poco X6 Pro"],
        "Vivo": ["Vivo X100 Pro", "Vivo X100", "Vivo V30 Pro", "Vivo V30", "Vivo T3 5G", "Vivo Y200 5G"],
        "Oppo": ["Oppo Find X7 Ultra", "Oppo Find N3", "Oppo Reno 12 Pro", "Oppo Reno 12", "Oppo Reno 11 Pro", "Oppo F27 Pro+"],
        "Motorola": ["Edge 50 Ultra", "Edge 50 Pro", "Edge 50 Fusion", "Moto G85", "Razr 50 Ultra", "Razr 50"],
        "Nothing": ["Nothing Phone (2)", "Nothing Phone (2a)", "Nothing Phone (1)", "CMF Phone 1"],
        "Realme": ["Realme GT 6", "Realme GT 6T", "Realme 12 Pro+", "Realme 12 Pro", "Realme 12 5G", "Realme Narzo 70 Pro"]
    },
    "Laptops": {
        "Apple": ["MacBook Pro 16 M3 Max", "MacBook Pro 14 M3 Pro", "MacBook Pro 14 M3", "MacBook Air 15 M3", "MacBook Air 13 M3", "MacBook Air 13 M2"],
        "Dell": ["XPS 15", "XPS 13 Plus", "XPS 13", "Inspiron 16", "Inspiron 15", "Inspiron 14 2-in-1", "G16 Gaming", "G15 Gaming"],
        "HP": ["Spectre x360 16", "Spectre x360 14", "Envy x360 15", "Pavilion Plus 14", "Pavilion 15", "Victus 16", "Victus 15", "Omen 16", "Omen Transcend 14"],
        "Lenovo": ["ThinkPad X1 Carbon Gen 11", "ThinkPad T14 Gen 4", "Yoga Book 9i", "Yoga Pro 7i", "Yoga 7i", "IdeaPad Slim 5", "IdeaPad Slim 3", "Legion Pro 7i", "Legion Slim 5"],
        "Asus": ["ROG Zephyrus G16", "ROG Zephyrus G14", "ROG Strix SCAR 16", "Zenbook 14 OLED", "Zenbook Duo OLED", "Vivobook 16", "Vivobook 15", "TUF Gaming F15", "TUF Gaming A15"],
        "Acer": ["Predator Helios 16", "Predator Triton 14", "Nitro 5", "Nitro 16", "Swift Go 14", "Swift Edge 16", "Aspire 7", "Aspire 5"]
    },
    "Headphones": {
        "Sony": ["WH-1000XM5", "WH-1000XM4", "WF-1000XM5", "WF-1000XM4", "WH-CH720N", "WH-CH520", "LinkBuds S", "LinkBuds", "WI-C100"],
        "Bose": ["QuietComfort Ultra Headphones", "QuietComfort Ultra Earbuds", "QuietComfort Headphones", "QuietComfort II Earbuds", "Bose 700"],
        "Sennheiser": ["Momentum 4 Wireless", "Momentum True Wireless 4", "Accentum Plus Wireless", "Accentum Wireless", "HD 450BT", "HD 350BT"],
        "JBL": ["Tour One M2", "Tour Pro 2", "Live 770NC", "Live Pro 2", "Tune 770NC", "Tune 670NC", "Tune 230NC", "Wave Beam", "Wave Flex"],
        "Apple": ["AirPods Max", "AirPods Pro (2nd Gen)", "AirPods (3rd Gen)", "AirPods (2nd Gen)", "Beats Studio Pro", "Beats Solo 4", "Beats Fit Pro", "Beats Studio Buds"]
    },
    "TVs": {
        "Samsung": ["Neo QLED 8K", "Neo QLED 4K", "OLED S95C Series", "The Frame", "Crystal 4K UHD", "Smart TV FHD"],
        "LG": ["OLED G3 Series", "OLED C3 Series", "OLED B3 Series", "QNED 83 Series", "UHD UR7500", "Smart TV LED"],
        "Sony": ["Bravia XR OLED A80L", "Bravia XR Mini LED X95L", "Bravia X90L", "Bravia X80L", "Bravia X74L"],
        "Xiaomi": ["Smart TV X Series", "Xiaomi TV Q2 QLED", "Redmi Smart TV", "Xiaomi TV A2 LED"],
        "TCL": ["C845 Mini LED", "C745 QLED", "C645 QLED", "P745 4K UHD", "S5400 FHD"],
        "Hisense": ["UX Series Mini LED", "U8K Mini LED", "U7K Mini LED", "A6K 4K UHD", "E4G FHD"]
    },
    "Cameras": {
        "Canon": ["EOS R3", "EOS R5", "EOS R6 Mark II", "EOS R10", "EOS R50", "EOS M50 Mark II", "PowerShot G7 X Mark III"],
        "Sony": ["Alpha 1", "Alpha 7R V", "Alpha 7 IV", "Alpha 7S III", "Alpha 6700", "ZV-E10", "ZV-1 II"],
        "Nikon": ["Z9", "Z8", "Z6 II", "Z5", "Z50", "Z fc", "D850", "D5600"],
        "Fujifilm": ["GFX 100 II", "X-T5", "X-T30 II", "X-S20", "X100VI", "Instax Mini 12", "Instax Mini Evo"],
        "Panasonic": ["Lumix S5 II", "Lumix GH6", "Lumix G9 II", "Lumix G100", "Lumix FZ80"]
    },
    "Smartwatches": {
        "Apple": ["Watch Ultra 2", "Watch Series 9", "Watch SE (2nd Gen)", "Watch Series 8", "Watch Ultra"],
        "Samsung": ["Galaxy Watch 6 Classic", "Galaxy Watch 6", "Galaxy Watch 5 Pro", "Galaxy Watch 5", "Galaxy Watch FE"],
        "Garmin": ["Fenix 7 Pro", "Forerunner 965", "Venu 3", "Instinct 2 Solar", "Forerunner 265", "Lily 2"],
        "Fitbit": ["Sense 2", "Versa 4", "Charge 6", "Inspire 3", "Luxe"],
        "Amazfit": ["GTR 4", "GTS 4", "Balance", "T-Rex 2", "Active Edge", "Bip 5", "Pop 3S"]
    },
    "Audio Speakers": {
        "JBL": ["Boombox 3", "Xtreme 4", "Charge 5", "Flip 6", "Go 4", "PartyBox 310", "Authentics 300"],
        "Sony": ["SRS-XV900", "SRS-XG300", "SRS-XE300", "SRS-XE200", "SRS-XB100", "HT-S20R Soundbar"],
        "Bose": ["SoundLink Revolve+", "SoundLink Flex", "Bose Smart Ultra Soundbar", "Bose Home Speaker 500"],
        "Marshall": ["Woburn III", "Stanmore III", "Acton III", "Middleton", "Emberton II", "Willen"],
        "Harman Kardon": ["Onyx Studio 8", "Aura Studio 4", "Go + Play 3", "SoundSticks 4"]
    },
    "Gaming Consoles": {
        "Sony": ["PlayStation 5 Slim", "PlayStation 5 Digital", "PlayStation Portal", "PlayStation VR2", "DualSense Edge Controller"],
        "Microsoft": ["Xbox Series X", "Xbox Series S", "Xbox Wireless Controller", "Xbox Elite Series 2"],
        "Nintendo": ["Switch OLED", "Switch Lite", "Switch Classic", "Nintendo Switch Pro Controller"],
        "Valve": ["Steam Deck OLED", "Steam Deck LCD"],
        "Asus": ["ROG Ally X", "ROG Ally Extreme"]
    },
    "Appliances": {
        "Dyson": ["V15 Detect Vacuum", "V12 Detect Slim", "Dyson Purifier Hot+Cool", "Dyson Supersonic Hair Dryer", "Airstrait Straightener"],
        "Samsung": ["Side-by-Side Refrigerator", "Double Door Refrigerator", "Front Load Washing Machine", "Convection Microwave Oven"],
        "LG": ["InstaView Refrigerator", "Smart Inverter Refrigerator", "AI Direct Drive Washer", "Charcoal Microwave Oven"],
        "Philips": ["Air Fryer XL", "Garment Steamer", "Sonicare Toothbrush", "Philips Shaver Series 5000", "Daily Collection Kettle"],
        "Bosch": ["13 Place Settings Dishwasher", "Front Load Washing Machine", "TrueMixx Pro Mixer Grinder"]
    },
    "Monitors": {
        "LG": ["UltraGear OLED 34", "UltraGear OLED 27", "UltraGear 27 Nano IPS", "LG DualUp 28", "LG UltraFine 32 4K"],
        "Dell": ["UltraSharp 32 4K", "UltraSharp 27 USB-C Hub", "P2723D 27", "S2721HN 27", "Alienware QD-OLED 34"],
        "Samsung": ["Odyssey G95SC QD-OLED", "Odyssey G8 OLED", "Odyssey G7", "Samsung Smart Monitor M8", "Samsung ViewFinity S8"],
        "BenQ": ["DesignVue PD3205U 4K", "PhotoVue SW271C", "Mobiuz EX2710S Gaming", "Zowie XL2546K E-Sports"]
    }
}

SPECIFICATIONS = {
    "Smartphones": {
        "RAM": ["8 GB", "12 GB", "16 GB"],
        "Storage": ["128 GB", "256 GB", "512 GB"],
        "Processor": ["Snapdragon 8 Gen 3", "Apple A17 Pro", "Tensor G3", "MediaTek Dimensity 9300"],
        "Battery": ["4500 mAh", "5000 mAh", "4300 mAh"],
        "Camera": ["50MP + 12MP + 10MP", "48MP + 12MP + 12MP", "200MP + 50MP + 12MP + 10MP"]
    },
    "Laptops": {
        "RAM": ["8 GB", "16 GB", "32 GB"],
        "Storage": ["512 GB SSD", "1 TB SSD", "2 TB SSD"],
        "Processor": ["Intel Core i7 13th Gen", "AMD Ryzen 7 7000 Series", "Apple M3 Chip", "Intel Core i5 12th Gen"],
        "Graphics": ["Intel Iris Xe", "NVIDIA RTX 4060", "Apple M3 10-core GPU", "NVIDIA RTX 4050"],
        "Display Size": ["13.3 inch", "14 inch", "15.6 inch", "16 inch"]
    },
    "Headphones": {
        "Type": ["Over Ear", "In Ear", "On Ear"],
        "ANC": ["Yes", "No"],
        "Battery Life": ["30 Hours", "40 Hours", "50 Hours", "24 Hours"],
        "Bluetooth Version": ["5.3", "5.2", "5.0"],
        "Driver Size": ["40 mm", "12 mm", "10 mm", "6 mm"]
    },
    "TVs": {
        "Display Type": ["OLED", "QLED", "LED", "Mini LED"],
        "Resolution": ["4K Ultra HD (3840 x 2160)", "Full HD (1920 x 1080)"],
        "Refresh Rate": ["60 Hz", "120 Hz", "144 Hz"],
        "Smart OS": ["Google TV", "Tizen OS", "WebOS", "Fire TV OS"],
        "Sound Output": ["20 W", "40 W", "60 W", "30 W"]
    },
    "Cameras": {
        "Sensor Type": ["Full Frame", "APS-C", "Micro Four Thirds"],
        "Megapixels": ["24.2 MP", "33.0 MP", "45.0 MP", "20.9 MP"],
        "Video Quality": ["4K 60p", "4K 120p", "8K 30p", "1080p 60p"],
        "Lens Included": ["18-45mm Kit Lens", "28-70mm Zoom Lens", "Body Only"],
        "ISO Range": ["100 - 51200", "100 - 102400", "100 - 25600"]
    },
    "Smartwatches": {
        "Display": ["AMOLED 1.5 inch", "LTPO OLED 1.9 inch", "Transflective Memory-in-Pixel"],
        "Battery Life": ["Up to 36 Hours", "Up to 18 Hours", "Up to 14 Days", "Up to 6 Days"],
        "GPS": ["Dual-frequency GPS", "Built-in GPS", "Connected GPS"],
        "Sensors": ["Heart Rate, SpO2, ECG, Temp", "Heart Rate, SpO2, Skin Temp", "Heart Rate, SpO2"],
        "Water Resistance": ["50m (5 ATM)", "100m (10 ATM)", "IP68"]
    },
    "Audio Speakers": {
        "Type": ["Portable Bluetooth", "Home Wired", "Smart Speaker"],
        "Output Power": ["10W", "30W", "80W", "150W"],
        "Battery Life": ["Up to 12 Hours", "Up to 20 Hours", "Up to 24 Hours", "N/A (AC Powered)"],
        "Waterproofing": ["IP67 Dust & Water Resistant", "IPX7 Waterproof", "No Waterproofing"],
        "Multi-speaker Connection": ["Yes", "No"]
    },
    "Gaming Consoles": {
        "Storage": ["1 TB SSD", "825 GB SSD", "512 GB SSD", "64 GB eMMC"],
        "Supported Resolution": ["4K at 120Hz", "1080p at 60Hz", "4K at 60Hz"],
        "Type": ["Home Console", "Handheld Console", "Accessory"],
        "Media Type": ["Blu-ray + Digital", "Digital Only", "Cartridge"],
        "Online Service": ["PlayStation Network", "Xbox Live", "Nintendo Online"]
    },
    "Appliances": {
        "Power Consumption": ["1200 W", "2000 W", "250 W", "350 kWh/year"],
        "Capacity/Size": ["350 Litres", "8 Kg", "28 Litres", "N/A"],
        "Control Type": ["Touch Control", "App Controlled", "Mechanical Knobs"],
        "Inverter Motor": ["Yes", "No", "N/A"],
        "Warranty": ["1 Year Product, 10 Years Motor", "2 Years Comprehensive", "1 Year"]
    },
    "Monitors": {
        "Screen Size": ["27 inch", "32 inch", "34 inch ultrawide", "28 inch DualUp"],
        "Panel Type": ["IPS", "VA", "OLED", "QD-OLED"],
        "Resolution": ["2560 x 1440 (2K)", "3840 x 2160 (4K)", "3440 x 1440 (UWQHD)"],
        "Refresh Rate": ["60 Hz", "144 Hz", "240 Hz", "75 Hz"],
        "Response Time": ["0.03 ms", "1 ms", "4 ms", "5 ms"]
    }
}

MODEL_SPECIFIC_IMAGES = {}

def get_product_image(full_name: str, category: str) -> str:
    # Use the smartphone-specific mockup image for the Smartphones category
    if category == "Smartphones":
        return "img/smartphone.png"
    # Use the laptop-specific mockup image for the Laptops category
    if category == "Laptops":
        return "img/laptop.jpg"
    # Use the headphones-specific mockup image for the Headphones category
    if category == "Headphones":
        return "img/headphones.jpg"
    # Use the TV-specific mockup image for the TVs category
    if category == "TVs":
        return "img/tv.jpg"
    # Use the camera-specific mockup image for the Cameras category
    if category == "Cameras":
        return "img/camera.jpg"
    # Use the smartwatch-specific mockup image for the Smartwatches category
    if category == "Smartwatches":
        return "img/smartwatch.png"
    # Use the speaker-specific mockup image for the Audio Speakers category
    if category == "Audio Speakers":
        return "img/speaker.jpg"
    # Use the gaming-specific mockup image for the Gaming Consoles category
    if category == "Gaming Consoles":
        return "img/gaming.png"
    # Use the appliance-specific mockup image for the Appliances category
    if category == "Appliances":
        return "img/appliances.jpg"
    # Use the monitor-specific mockup image for the Monitors category
    if category == "Monitors":
        return "img/monitors.jpg"
    # Return the user-uploaded premium collage image containing all tech products in one place for other categories
    return "img/placeholder.jpg"

REVIEW_POOL = [
    # Positive
    {"rating": 5.0, "title": "Absolutely outstanding", "text": "This product exceeded all my expectations. The build quality is amazing, performance is top-notch, and it functions flawlessly. High recommend!"},
    {"rating": 5.0, "title": "Highly recommended", "text": "Best purchase I have made this year. Super durable, efficient, and delivers exactly what is promised. Great value for money."},
    {"rating": 4.0, "title": "Very good product", "text": "Very happy with the purchase. The features are excellent, works super fast. Only minor complaint is that the battery life could be slightly better, but otherwise perfect."},
    {"rating": 4.5, "title": "Great value", "text": "Amazing feature list for this price point. It holds up exceptionally well compared to higher priced models. Highly user friendly layout."},
    
    # Neutral
    {"rating": 3.0, "title": "Decent, but average", "text": "It works as advertised, but it is nothing special. The quality is decent, but there are better options available in this price range. Average battery and look."},
    {"rating": 3.5, "title": "Good, but has minor issues", "text": "The performance is stable, but setup was slightly complicated. Customer service was slow to respond. It gets the job done but could be better optimized."},
    
    # Negative
    {"rating": 2.0, "title": "Disappointed", "text": "Not worth the money. It feels cheap and started lagging within a few days of use. Battery drains rapidly and it overheats constantly. Would not recommend."},
    {"rating": 1.0, "title": "Waste of money", "text": "Total failure. It stopped working after one week. The screen has glitch issues and the packaging was damaged when it arrived. Returning immediately."}
]

SOURCES = ["Amazon", "Flipkart", "Croma", "Reliance Digital", "Vijay Sales"]

CATEGORY_NOUNS = {
    "Smartphones": "phone",
    "Laptops": "laptop",
    "Headphones": "headphones",
    "TVs": "TV",
    "Cameras": "camera",
    "Smartwatches": "smartwatch",
    "Audio Speakers": "speaker",
    "Gaming Consoles": "console",
    "Appliances": "appliance",
    "Monitors": "monitor"
}

def generate_store_url(source: str, product_name: str, category: str) -> str:
    # Build clean query parameter from product name and specifications
    query_param = product_name.replace(" ", "+")
    
    if source == "Amazon":
        domain = "amazon.in"
    elif source == "Flipkart":
        domain = "flipkart.com"
    elif source == "Croma":
        domain = "croma.com"
    elif source == "Reliance Digital":
        domain = "reliancedigital.in"
    elif source == "Vijay Sales":
        domain = "vijaysales.com"
    else:
        domain = ""
        
    if domain:
        return f"https://www.google.com/search?q=site:{domain}+{query_param}"
    return f"https://www.google.com/search?q={query_param}"


def generate_specifications(category: str) -> Dict[str, Any]:
    specs = {}
    if category in SPECIFICATIONS:
        for k, v in SPECIFICATIONS[category].items():
            specs[k] = random.choice(v)
    return specs

def generate_reviews(avg_rating: float) -> List[Dict[str, Any]]:
    # Generate 5-10 random reviews aligned with target rating
    count = random.randint(5, 10)
    reviews = []
    
    # Choose review pool based on target rating
    for _ in range(count):
        if avg_rating >= 4.2:
            # Shift weight towards positive
            weights = [0.4, 0.4, 0.15, 0.05, 0.0, 0.0, 0.0, 0.0]
        elif avg_rating >= 3.5:
            weights = [0.2, 0.2, 0.3, 0.2, 0.05, 0.05, 0.0, 0.0]
        else:
            weights = [0.0, 0.0, 0.1, 0.1, 0.3, 0.3, 0.1, 0.1]
            
        weights = weights[:len(REVIEW_POOL)]
        # Normalize weights
        s = sum(weights)
        weights = [w / s for w in weights]
        
        template = random.choices(REVIEW_POOL, weights=weights, k=1)[0]
        author = random.choice(["Amit Kumar", "Sneha S.", "Rahul Verma", "Pooja Mehta", "John D.", "Vikram R.", "Ananya Sen", "Rajesh P."])
        reviews.append({
            "author": author,
            "rating": max(1.0, min(5.0, template["rating"] + random.choice([-0.5, 0, 0.5]))),
            "title": template["title"],
            "text": template["text"]
        })
        
    # Inject a potential mock fake review (25% chance)
    if random.random() < 0.25:
        fake_type = random.choice(["caps", "short_extreme", "mismatch", "duplicate"])
        if fake_type == "caps":
            reviews.append({
                "author": "Anonymous Buyer",
                "rating": 5.0,
                "title": "AMAZING!!!",
                "text": "THIS IS THE BEST PRODUCT EVER!!! I LOVE IT SO MUCH AND RECOMMENDED TO EVERYONE!!! BUY NOW!!!"
            })
        elif fake_type == "short_extreme":
            reviews.append({
                "author": "Anonymous",
                "rating": 5.0,
                "title": "Nice",
                "text": "Good phone."
            })
        elif fake_type == "mismatch":
            reviews.append({
                "author": "Rajesh K.",
                "rating": 1.0,
                "title": "Excellent",
                "text": "This product is amazing, fast delivery, and perfect packaging! Love it!"
            })
        elif fake_type == "duplicate":
            dup_text = "Standard average product. Disappointed with the quality and delivery."
            reviews.append({
                "author": "User A",
                "rating": 2.0,
                "title": "Poor",
                "text": dup_text
            })
            reviews.append({
                "author": "User B",
                "rating": 2.0,
                "title": "Average",
                "text": dup_text
            })
    return reviews

def get_logical_base_price(category: str, brand: str, model: str) -> float:
    name = model.lower()
    
    if category == "Smartphones":
        if "fold" in name:
            return 164999.0
        if "ultra" in name:
            return 129999.0
        if "pro max" in name:
            if "17" in name: return 159900.0
            if "16" in name: return 144900.0
            if "15" in name: return 134900.0
            if "14" in name: return 119900.0
            return 109900.0
        if "pro xl" in name:
            return 124999.0
        if "pro" in name:
            if "apple" in name or "iphone" in name or brand.lower() == "apple":
                if "17" in name: return 139900.0
                if "16" in name: return 119900.0
                if "15" in name: return 109900.0
                return 89900.0
            if "google" in name or "pixel" in name or brand.lower() == "google":
                return 109999.0
            if "samsung" in name or "s2" in name or brand.lower() == "samsung":
                return 79999.0
            return 49999.0
        if "plus" in name or "s26+" in name or "s25+" in name or "s24+" in name:
            if "17" in name: return 99900.0
            if "16" in name: return 89900.0
            if "15" in name: return 79900.0
            if "s26" in name: return 89999.0
            if "s25" in name: return 84999.0
            if "s24" in name: return 84999.0
            return 69900.0
        if "flip" in name:
            return 99999.0
        if "lite" in name or "13c" in name or "cmf" in name or "y200" in name or "t3" in name:
            return 14999.0
        if "ce4" in name or "nord" in name or "a35" in name or "m55" in name or "f55" in name:
            return 24999.0
        if "a55" in name or "12r" in name or "11r" in name or "13r" in name:
            return 39999.0
        # Standard flagship
        if "17" in name: return 89900.0
        if "16" in name: return 79900.0
        if "15" in name: return 69900.0
        if "14" in name: return 59900.0
        if "s26" in name: return 79999.0
        if "s25" in name: return 74999.0
        if "s24" in name: return 74999.0
        if "s23" in name: return 64999.0
        if "oneplus 13" in name or "oneplus 12" in name: return 64999.0
        if "pixel 10" in name: return 79999.0
        if "pixel 9" in name: return 75999.0
        if "pixel 8" in name: return 69999.0
        return 29999.0
        
    elif category == "Laptops":
        if "m3 max" in name: return 249900.0
        if "m3 pro" in name: return 199900.0
        if "m3" in name: return 114900.0
        if "m2" in name: return 99900.0
        if "carbon" in name or "spectre" in name or "xps 15" in name or "zenbook duo" in name or "predator helios" in name or "legion pro" in name or "omen" in name:
            return 149900.0
        if "yoga 9" in name or "zenbook" in name or "rog" in name or "triton" in name:
            return 119900.0
        if "yoga 7" in name or "nitro" in name or "victus" in name or "g15" in name or "g16" in name or "thinkpad" in name or "swift" in name:
            return 74900.0
        if "inspiron" in name or "pavilion" in name or "ideapad slim 5" in name or "aspire 7" in name:
            return 54900.0
        return 39900.0
        
    elif category == "Headphones":
        if "ultra" in name or "xm5" in name or "momentum 4" in name:
            return 29990.0
        if "xm4" in name or "quietcomfort" in name:
            return 23990.0
        if "accentum" in name or "770nc" in name or "660nc" in name or "studio pro" in name:
            return 14990.0
        if "ch720n" in name or "tour" in name or "live" in name:
            return 9990.0
        if "wave" in name or "ch520" in name or "c100" in name:
            return 3499.0
        return 5999.0
        
    elif category == "TVs":
        if "8k" in name or "g3" in name:
            return 249990.0
        if "c3" in name or "oled a80" in name or "ux series" in name:
            return 169990.0
        if "b3" in name or "neo qled 4k" in name or "mini led" in name:
            return 149990.0
        if "the frame" in name or "qned" in name or "q2 qled" in name or "c745" in name:
            return 84990.0
        if "crystal 4k" in name or "ur7500" in name or "x80l" in name or "x74l" in name:
            return 49990.0
        if "smart tv" in name or "redmi" in name or "s5400" in name:
            return 15999.0
        return 29999.0
        
    elif category == "Cameras":
        if "alpha 1" in name or "z9" in name or "gfx 100" in name:
            return 549990.0
        if "eos r3" in name or "alpha 7r" in name or "z8" in name:
            return 349990.0
        if "eos r5" in name or "d850" in name:
            return 329995.0
        if "eos r6" in name or "alpha 7 iv" in name or "z6 ii" in name or "x-t5" in name:
            return 179990.0
        if "alpha 6700" in name or "x-s20" in name or "lumix s5" in name:
            return 129990.0
        if "eos r10" in name or "x-t30" in name or "z50" in name or "lumix gh6" in name:
            return 79990.0
        if "r50" in name or "m50" in name or "zv-e10" in name or "z fc" in name or "d5600" in name:
            return 57995.0
        if "instax" in name or "powershot" in name or "zv-1" in name:
            return 14990.0
        return 49990.0
        
    elif category == "Smartwatches":
        if "ultra" in name or "fenix" in name:
            return 81990.0
        if "forerunner 9" in name:
            return 67490.0
        if "venu" in name or "watch series" in name:
            return 41900.0
        if "galaxy watch 6 classic" in name or "forerunner 2" in name:
            return 36999.0
        if "galaxy watch 6" in name or "watch se" in name or "sense 2" in name:
            return 29999.0
        if "watch 5" in name or "versa 4" in name or "gtr" in name or "gts" in name:
            return 19999.0
        if "charge 6" in name or "inspire 3" in name or "bip" in name:
            return 11999.0
        return 4999.0
        
    elif category == "Audio Speakers":
        if "woburn" in name or "xv900" in name or "partybox" in name:
            return 59999.0
        if "stanmore" in name or "authentics" in name or "home speaker 500" in name:
            return 34500.0
        if "boombox" in name or "xtreme" in name or "xg300" in name or "revolve+" in name:
            return 29999.0
        if "acton" in name or "middleton" in name or "flex" in name or "aura" in name:
            return 15900.0
        if "emberton" in name or "charge" in name or "xe300" in name:
            return 13990.0
        if "flip" in name or "xe200" in name or "go + play" in name:
            return 9999.0
        if "xb100" in name or "go 4" in name or "willen" in name:
            return 3990.0
        return 7990.0
        
    elif category == "Gaming Consoles":
        if "vr2" in name:
            return 57990.0
        if "xbox series x" in name or "playstation 5" in name or "steam deck oled" in name:
            return 48990.0
        if "rog ally" in name or "xbox series s" in name:
            return 34990.0
        if "switch oled" in name or "steam deck" in name:
            return 30999.0
        if "portal" in name or "switch lite" in name:
            return 17499.0
        if "controller" in name:
            return 5990.0
        return 24990.0
        
    elif category == "Appliances":
        if "side-by-side" in name or "instaview" in name:
            return 89990.0
        if "v15" in name or "purifier" in name:
            return 59900.0
        if "supersonic" in name or "airstrait" in name:
            return 49900.0
        if "direct drive" in name or "front load" in name:
            return 39990.0
        if "double door" in name or "dishwasher" in name:
            return 35990.0
        if "microwave" in name or "air fryer" in name:
            return 18990.0
        if "shaver" in name or "toothbrush" in name or "mixer" in name:
            return 5990.0
        return 14990.0
        
    elif category == "Monitors":
        if "odyssey g9" in name or "alienware" in name:
            return 139999.0
        if "ultragear oled" in name or "ultrasharp 32" in name:
            return 99999.0
        if "dualup" in name or "odyssey g7" in name or "smart monitor" in name:
            return 49999.0
        if "ultrasharp 27" in name or "viewfinity" in name or "designvue" in name:
            return 39999.0
        if "p2723d" in name or "ultragear 27" in name or "mobiuz" in name:
            return 24999.0
        return 14999.0
        
    return 19999.0

def seed_database():
    db = get_db()
    products_col = db["products"]
    
    print("Clearing products collection before seeding...")
    products_col.delete_many({})
        
    print("Seeding database with simulated comparison data...")
    all_products = []
    
    # Base prices to make them consistent across stores
    base_prices = {
        "iPhone 17 Pro Max": 159900,
        "iPhone 17 Pro": 139900,
        "iPhone 17": 89900,
        "iPhone 16 Pro": 129900,
        "iPhone 16": 79900,
        "iPhone 15 Pro": 134900,
        "iPhone 15": 79900,
        "iPhone 14": 69900,
        "Galaxy S26 Ultra": 139999,
        "Galaxy S26": 79999,
        "Galaxy S25 Ultra": 129999,
        "Galaxy S25": 74999,
        "Galaxy S24 Ultra": 129999,
        "Galaxy S24": 74999,
        "Galaxy A55": 39999,
        "OnePlus 14 Pro": 79999,
        "OnePlus 14": 69999,
        "OnePlus 13": 64999,
        "OnePlus 12": 64999,
        "OnePlus 12R": 39999,
        "OnePlus Nord CE4": 24999,
        "Pixel 10 Pro": 119999,
        "Pixel 10": 79999,
        "Pixel 9 Pro": 109999,
        "Pixel 9": 75999,
        "Pixel 8 Pro": 109999,
        "Pixel 8": 75999,
        "Pixel 7a": 43999,
        
        "MacBook Pro M3": 169900,
        "MacBook Air M3": 114900,
        "MacBook Air M2": 99900,
        "XPS 13": 145000,
        "Inspiron 15": 54000,
        "G15 Gaming": 75000,
        "Spectre x360": 125000,
        "Pavilion 15": 62000,
        "Victus 16": 72000,
        "ThinkPad X1 Carbon": 185000,
        "Yoga 7i": 89000,
        "IdeaPad Slim 3": 38000,
        "ROG Zephyrus G14": 135000,
        "Zenbook 14": 82000,
        "Vivobook 15": 42000,
        
        "WH-1000XM5": 29990,
        "WF-1000XM5": 23990,
        "WH-CH720N": 9990,
        "QuietComfort Ultra": 35900,
        "QuietComfort II": 27900,
        "Bose 700": 32900,
        "Momentum 4": 34990,
        "Accentum Plus": 15990,
        "HD 450BT": 8990,
        "Tune 770NC": 6999,
        "Live 660NC": 11999,
        "Wave Beam": 3499,
        
        "Neo QLED 4K": 149990,
        "Crystal 4K UHD": 32990,
        "The Frame": 89990,
        "OLED C3 Series": 169990,
        "QNED 83 Series": 84990,
        "UHD UR7500": 34990,
        "Bravia XR OLED": 219900,
        "Bravia X80L": 74900,
        "Bravia X74L": 52900,
        "Smart TV X Series": 22999,
        "Redmi Smart TV": 13999,
        "Xiaomi TV Q2": 49999,
        
        "EOS R5": 329995,
        "EOS R10": 75995,
        "EOS M50 Mark II": 57995,
        "Alpha 7 IV": 218990,
        "Alpha 6700": 136990,
        "ZV-E10": 61490,
        "Z6 II": 154990,
        "Z50": 72990,
        "D5600": 53450,
        "X-T5": 169999,
        "X-S20": 118999,
        "X-T30 II": 88999,

        # Smartwatches
        "Watch Ultra 2": 89900,
        "Watch Series 9": 41900,
        "Watch SE": 29900,
        "Galaxy Watch 6 Classic": 36999,
        "Galaxy Watch 6": 29999,
        "Galaxy Watch 5 Pro": 39999,
        "Fenix 7 Pro": 81990,
        "Forerunner 965": 67490,
        "Venu 3": 44990,
        "Sense 2": 24999,
        "Versa 4": 20499,
        "Charge 6": 14999,

        # Audio Speakers
        "Boombox 3": 39999,
        "Xtreme 4": 29999,
        "Flip 6": 9999,
        "SRS-XG300": 24990,
        "SRS-XE300": 13990,
        "SRS-XB100": 3990,
        "SoundLink Revolve+": 24500,
        "SoundLink Flex": 15900,
        "Bose Home Speaker 500": 34500,
        "Woburn III": 59999,
        "Stanmore III": 37999,
        "Emberton II": 14999,

        # Gaming Consoles
        "PlayStation 5 Slim": 44990,
        "PlayStation 5 Portal": 18990,
        "PlayStation VR2": 57990,
        "Xbox Series X": 48990,
        "Xbox Series S": 34990,
        "Xbox Wireless Controller": 5990,
        "Switch OLED": 30999,
        "Switch Lite": 17499,
        "Switch Classic": 25999,

        # Appliances
        "V15 Detect Vacuum": 65900,
        "Purifier Hot+Cool": 59900,
        "Supersonic Hair Dryer": 49900,
        "Double Door Refrigerator": 35990,
        "Front Load Washer": 38990,
        "Convection Microwave": 18990,
        "Side-by-Side Refrigerator": 89990,
        "Direct Drive Washer": 42990,
        "LG Charcoal Microwave": 22990,

        # Monitors
        "UltraGear OLED 34": 99999,
        "UltraGear 27": 24999,
        "LG DualUp 28": 54999,
        "UltraSharp 32 4K": 84999,
        "P2723D 27": 29999,
        "Alienware QD-OLED 34": 119999,
        "Odyssey G95SC": 149999,
        "Odyssey G7": 49999,
        "Samsung Smart Monitor M8": 44999
    }
    
    # We will generate different variations of specs for each model, but keep them generally matching.
    # We also keep specifications constant for the same model across stores
    model_specs_cache = {}

    for category, brands in BRANDS_CATEGORIES.items():
        for brand, models in brands.items():
            for model in models:
                full_name = model if model.startswith(brand) else f"{brand} {model}"
                if model in base_prices:
                    base_price = base_prices[model]
                else:
                    base_price = get_logical_base_price(category, brand, model)
                
                # Cache specifications for this model
                if full_name not in model_specs_cache:
                    model_specs_cache[full_name] = generate_specifications(category)
                specs = model_specs_cache[full_name]
                
                # Base parameters for quality (to make sure Amazon / Flipkart models have similar ratings)
                base_rating = round(random.uniform(3.8, 4.8), 1)
                
                # Generate source variants (Amazon, Flipkart, Croma)
                for source in SOURCES:
                    # Vary price by +/- 4%
                    price_var = random.uniform(-0.04, 0.04)
                    price = round(base_price * (1 + price_var), -2) # Round to nearest 100
                    
                    # Vary rating slightly
                    rating = round(max(1.0, min(5.0, base_rating + random.uniform(-0.2, 0.2))), 1)
                    review_count = random.randint(100, 5000)
                    
                    reviews = generate_reviews(rating)
                    
                    # Generate 90-day price history ending with current price
                    import datetime
                    import math
                    price_history = []
                    current_date = datetime.date(2026, 6, 2)
                    for d_offset in range(89, -1, -1):
                        hist_date = current_date - datetime.timedelta(days=d_offset)
                        if d_offset == 0:
                            hist_price = float(price)
                        else:
                            # Fluctuates around final price with a weekly cycle plus random noise
                            weekly_cycle = math.sin(d_offset * (2 * math.pi / 7)) * 0.02
                            random_noise = random.uniform(-0.015, 0.015)
                            hist_var = weekly_cycle + random_noise
                            hist_price = float(round(price * (1 + hist_var), -2))
                        price_history.append({
                            "date": hist_date.strftime("%Y-%m-%d"),
                            "price": hist_price
                        })
                    
                    product_doc = {
                        "name": full_name,
                        "category": category,
                        "brand": brand,
                        "price": float(price),
                        "currency": "INR",
                        "source": source,
                        "url": generate_store_url(source, full_name, category),
                        "image_url": get_product_image(full_name, category),
                        "rating": float(rating),
                        "review_count": int(review_count),
                        "reviews": reviews,
                        "specifications": specs,
                        "price_history": price_history
                    }
                    all_products.append(product_doc)
                    
    # Pre-score seeded products with ML features
    from backend.services.ml_engine import ml_engine
    scored_products = ml_engine.score_and_recommend(all_products)
    products_col.insert_many(scored_products)
    print(f"Database seeded with {len(scored_products)} products including 90-day price history and ML metrics.")

if __name__ == "__main__":
    seed_database()
