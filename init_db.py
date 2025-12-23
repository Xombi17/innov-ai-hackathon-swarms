from wellsync_ai.data.database import initialize_database
from wellsync_ai.utils.config import create_directories

if __name__ == "__main__":
    print("Initializing directories...")
    create_directories()
    print("Initializing database...")
    initialize_database()
    print("Done!")
