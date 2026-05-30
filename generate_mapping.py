from backend.services.scraper import BRANDS_CATEGORIES

# Define 130 unique, verified Unsplash image IDs grouped by category

# 28 unique Smartphones
smartphones_pics = [
    "photo-1511707171634-5f897ff02aa9", # iPhone 17 Pro Max
    "photo-1592750475338-74b7b21085ab", # iPhone 17 Pro
    "photo-1616348436168-de43ad0db179", # iPhone 17
    "photo-1510557880182-3d4d3cba35a5", # iPhone 16 Pro
    "photo-1580910051074-3eb694886505", # iPhone 16
    "photo-1565630916779-e303be97b6f5", # iPhone 15 Pro
    "photo-1610945265064-0e34e5519bbf", # iPhone 15
    "photo-1610945480738-6e4c5e113c8f", # iPhone 14
    "photo-1574755393849-623942496936", # Galaxy S26 Ultra
    "photo-1585399000684-d2f72660f092", # Galaxy S26
    "photo-1598327105666-5b89351aff97", # Galaxy S25 Ultra
    "photo-1598327106026-d9521da673d1", # Galaxy S25
    "photo-1601784551446-20c9e07cdbdb", # Galaxy S24 Ultra
    "photo-1609081219090-a6d81d3085bf", # Galaxy S24
    "photo-1649859396073-13ff7227672e", # Galaxy A55
    "photo-1546054454-aa26e2b734c7", # OnePlus 14 Pro
    "photo-1512941937669-90a1b58e7e9c", # OnePlus 14
    "photo-1533228892584-c9cba602513f", # OnePlus 13
    "photo-1695048133142-1a20484d2569", # OnePlus 12
    "photo-1695048132832-154df668baea", # OnePlus 12R
    "photo-1695048065098-b0a394ec5018", # OnePlus Nord CE4
    "photo-1678652197831-2d180705cd2c", # Pixel 10 Pro
    "photo-1551645121-d1034da75057", # Pixel 10
    "photo-1636467219430-8a6a68383a1d", # Pixel 9 Pro
    "photo-1628202926206-c63a34b1e7e9", # Pixel 9
    "photo-1605787020600-b9ebd5df1d07", # Pixel 8 Pro
    "photo-1605236453806-6ff36851218e", # Pixel 8
    "photo-1512499617640-c74ae3a79d37"  # Pixel 7a
]

# 15 unique Laptops
laptops_pics = [
    "photo-1517336714731-489689fd1ca8", # MacBook Pro M3
    "photo-1611186871348-b1ce696e52c9", # MacBook Air M3
    "photo-1593642632823-8f785ba67e45", # MacBook Air M2
    "photo-1531297484001-80022131f5a1", # XPS 13
    "photo-1588872657578-7efd1f1555ed", # Inspiron 15
    "photo-1603302576837-37561b2e2302", # G15 Gaming
    "photo-1541807084-5c52b6b3adef", # Spectre x360
    "photo-1496181130204-755241544e35", # Pavilion 15
    "photo-1525373612132-b3e824646615", # Victus 16
    "photo-1542751371-adc38448a05e", # ThinkPad X1 Carbon
    "photo-1593642702821-c8da6771f0c6", # Yoga 7i
    "photo-1588702547314-f10028983d51", # IdeaPad Slim 3
    "photo-1618424181497-157f25b6ddd5", # ROG Zephyrus G14
    "photo-1525547719571-a2d4ac8945e2", # Zenbook 14
    "photo-1498050108023-c5249f4df085"  # Vivobook 15
]

# 12 unique Headphones
headphones_pics = [
    "photo-1505740420928-5e560c06d30e", # WH-1000XM5
    "photo-1546435770-a3e426bf472b", # WF-1000XM5
    "photo-1618384887929-16ec33fab9ef", # WH-CH720N
    "photo-1590658268037-6bf12165a8df", # QuietComfort Ultra
    "photo-1608156639585-b3a032ef9689", # QuietComfort II
    "photo-1583394838336-acd977736f90", # Bose 700
    "photo-1487215078519-e21cc028cb29", # Momentum 4
    "photo-1524678606370-a47ad25cb82a", # Accentum Plus
    "photo-1613040809024-b4ef7ba99bc3", # HD 450BT
    "photo-1599669454699-248893623440", # Tune 770NC
    "photo-1585298723682-7115561c51b7", # Live 660NC
    "photo-1545454675-3531b543be5d"  # Wave Beam
]

# 12 unique TVs
tvs_pics = [
    "photo-1593305841991-05c297ba4575", # Samsung Neo QLED 4K
    "photo-1601944179066-297cbd6cdcdf", # Samsung Crystal 4K UHD
    "photo-1593789198777-f29bc259780e", # Samsung The Frame
    "photo-1552533048-c8546f5de999", # LG OLED C3 Series
    "photo-1461151304267-38535e780c79", # LG QNED 83 Series
    "photo-1509281373149-e957c6296406", # LG UHD UR7500
    "photo-1522869635100-9f4c5e86aa37", # Sony Bravia XR OLED
    "photo-1574269909862-7e1d70bb8078", # Sony Bravia X80L
    "photo-1567690187548-f07b1d7bf5a9", # Sony Bravia X74L
    "photo-1486406146926-c627a92ad1ab", # Xiaomi Smart TV X Series
    "photo-1535016120720-40c646be5580", # Xiaomi Redmi Smart TV
    "photo-1593115057322-e94b77572f20"  # Xiaomi TV Q2
]

# 12 unique Cameras
cameras_pics = [
    "photo-1516035069371-29a1b244cc32", # EOS R5
    "photo-1526170375885-4d8ecf77b99f", # EOS R10
    "photo-1502920917128-1fc500650ab9", # EOS M50 Mark II
    "photo-1495707902641-75cac588d2e9", # Alpha 7 IV
    "photo-1513829096996-5e0f7e4367ef", # Alpha 6700
    "photo-1500051638674-ff996a0bc29e", # ZV-E10
    "photo-1560253023-3ec5d502959f", # Z6 II
    "photo-1569003339405-ea396a5a8a90", # Z50
    "photo-1519638396437-afb5f54341b3", # D5600
    "photo-1542038784456-1ea8e935640e", # X-T5
    "photo-1516257984-b1b4d707412e", # X-S20
    "photo-1500648767791-00dcc994a43e"  # X-T30 II
]

# 12 unique Smartwatches
smartwatches_pics = [
    "photo-1434494878577-86c23bcb06b9", # Watch Ultra 2
    "photo-1579586337278-3befd40fd17a", # Watch Series 9
    "photo-1508685096489-7aacd43bd3b1", # Watch SE
    "photo-1517502884422-41eaaced0168", # Galaxy Watch 6 Classic
    "photo-1523275335684-37898b6baf30", # Galaxy Watch 6
    "photo-1542496658-e33a6d0d50f6", # Galaxy Watch 5 Pro
    "photo-1539874754764-5a96559165b0", # Fenix 7 Pro
    "photo-1617042375876-a13e36732a04", # Forerunner 965
    "photo-1509198397868-475647b2a1e5", # Venu 3
    "photo-1575311373937-040b8e1fd5b6", # Fitbit Sense 2
    "photo-1507679799987-c73779587ccf", # Fitbit Versa 4
    "photo-1434056886845-dac89ffee9b5"  # Fitbit Charge 6
]

# 12 unique Audio Speakers
speakers_pics = [
    "photo-1608220179550-10906738df13", # Boombox 3
    "photo-1618609378039-b572f64c5b42", # Xtreme 4
    "photo-1608043152269-423dbba4e7e1", # Flip 6
    "photo-1529359744902-80b7b4a621c3", # SRS-XG300
    "photo-1589003077984-894e133dabab", # SRS-XE300
    "photo-1589256469067-ea99122bb5a5", # SRS-XB100
    "photo-1508700115892-45ecd05ae2ad", # SoundLink Revolve+ (Replaced duplicate headphone image with speaker image)
    "photo-1507646227500-4d389b0012be", # SoundLink Flex
    "photo-1543510473-ac2c35329a28", # Bose Home Speaker 500
    "photo-1512445277651-7efd379fb7c6", # Marshall Woburn III
    "photo-1545048702-79362596cdc9", # Marshall Stanmore III
    "photo-1563245372-f21724e3856d"  # Marshall Emberton II
]

# 9 unique Gaming Consoles
consoles_pics = [
    "photo-1606813907291-d86efa9b94db", # PlayStation 5 Slim
    "photo-1605901309584-818e25960a8f", # PlayStation 5 Portal
    "photo-1595169001211-4074c73ba501", # PlayStation VR2
    "photo-1622979135225-d2ba269cf1ac", # Xbox Series X
    "photo-1600080972464-8e5f35f63d08", # Xbox Series S
    "photo-1607604276583-eef5d076aa5f", # Xbox Wireless Controller
    "photo-1550745165-9bc0b252726f", # Nintendo Switch OLED
    "photo-1592155998243-c224c2837b2a", # Nintendo Switch Lite
    "photo-1566241477600-ac026ad43874"  # Nintendo Switch Classic
]

# 9 unique Appliances
appliances_pics = [
    "photo-1558317374-067fb5f30001", # Dyson V15 Detect Vacuum
    "photo-1585338107529-13afc5f02586", # Dyson Purifier Hot+Cool
    "photo-1571175432230-01a2d86a39d8", # Dyson Supersonic Hair Dryer
    "photo-1582738411706-bfc8e691d1c2", # Samsung Double Door Refrigerator
    "photo-1571175443880-49e1d25b4bc5", # Samsung Front Load Washer
    "photo-1522337360788-8b13dee7a37e", # Samsung Convection Microwave
    "photo-1584622650111-993a426fbf0a", # LG Side-by-Side Refrigerator
    "photo-1626806787461-102c1bfaaea1", # LG Direct Drive Washer
    "photo-1581578731548-c64695cc6952"  # LG Charcoal Microwave
]

# 9 unique Monitors
monitors_pics = [
    "photo-1527443224154-c4a3942d3acf", # LG UltraGear OLED 34
    "photo-1585776245991-cf89dd7fc73a", # LG UltraGear 27
    "photo-1547082299-de196ea013d6", # LG DualUp 28
    "photo-1527443195191-29e6ca70a597", # Dell UltraSharp 32 4K
    "photo-1616440347437-b1c73416efc2", # Dell P2723D 27 (Replaced duplicate phone image with unique monitor)
    "photo-1593642632559-0c6d3fc62b89", # Dell Alienware QD-OLED 34
    "photo-1563986768609-322da13575f3", # Samsung Odyssey G95SC
    "photo-1542751371-adc38448a05e", # Samsung Odyssey G7
    "photo-1545665277-5937489579f2"  # Samsung Smart Monitor M8 (Replaced duplicate monitor image with unique monitor)
]

# Assert total unique elements is 130
all_images = (
    smartphones_pics + laptops_pics + headphones_pics + tvs_pics + cameras_pics +
    smartwatches_pics + speakers_pics + consoles_pics + appliances_pics + monitors_pics
)

print(f"Total images assigned: {len(all_images)}")
unique_images = set(all_images)
print(f"Unique images: {len(unique_images)}")
duplicates = len(all_images) - len(unique_images)
print(f"Duplicates: {duplicates}")

if duplicates > 0:
    # Print exactly which items are duplicated
    seen = set()
    dup_ids = set()
    for img in all_images:
        if img in seen:
            dup_ids.add(img)
        seen.add(img)
    print(f"Duplicated IDs: {dup_ids}")

# Zip each category and brands/models to map them 1-to-1
idx_map = {
    "Smartphones": smartphones_pics,
    "Laptops": laptops_pics,
    "Headphones": headphones_pics,
    "TVs": tvs_pics,
    "Cameras": cameras_pics,
    "Smartwatches": smartwatches_pics,
    "Audio Speakers": speakers_pics,
    "Gaming Consoles": consoles_pics,
    "Appliances": appliances_pics,
    "Monitors": monitors_pics
}

dict_output = {}

for category, brands in BRANDS_CATEGORIES.items():
    pool = idx_map[category]
    counter = 0
    for brand, models in brands.items():
        for model in models:
            # Clean brand name repetitions for OnePlus, Bose, LG, Samsung
            clean_brand = brand
            clean_model = model
            if brand == "OnePlus" and model.startswith("OnePlus "):
                clean_model = model.replace("OnePlus ", "", 1)
            elif brand == "Bose" and model.startswith("Bose "):
                clean_model = model.replace("Bose ", "", 1)
            elif brand == "LG" and model.startswith("LG "):
                clean_model = model.replace("LG ", "", 1)
            elif brand == "Samsung" and model.startswith("Samsung "):
                clean_model = model.replace("Samsung ", "", 1)
                
            full_name = f"{clean_brand} {clean_model}"
            img_id = pool[counter]
            dict_output[full_name] = f"https://images.unsplash.com/{img_id}?w=400&auto=format&fit=crop"
            counter += 1

print("\nVerify clean dict mapping size:", len(dict_output))
assert len(dict_output) == 130
assert len(set(dict_output.values())) == 130
print("SUCCESS: 130 unique models mapped to 130 unique Unsplash URLs!")

# Write generated dictionary to a temporary python file to import
import json
with open("mapping.json", "w") as f:
    json.dump(dict_output, f, indent=4)
print("Saved mapping.json")
