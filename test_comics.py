from comics import gocomics

def test_comic():
    try:
        # Try to get Calvin and Hobbes
        comic = gocomics.Calvin_and_Hobbes()
        latest = comic.get_latest()
        print("Latest comic:", latest)
        print("Image URL:", latest.image if hasattr(latest, 'image') else latest.image_url)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_comic()
