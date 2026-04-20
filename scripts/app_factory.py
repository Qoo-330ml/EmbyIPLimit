from __future__ import annotations

from emby_client import EmbyClient
from monitor import EmbyMonitor
from security import EmbySecurity
from shadow_library import ShadowLibrary
from shadow_library_syncer import ShadowLibrarySyncer
from storage.database_manager import DatabaseManager
from storage.media_request_store import WishStore
from tmdb_client import TMDBClient
from web.app_server import WebServer
from web.runtime import create_location_service


class EmbyQApp:
    def __init__(
        self,
        config,
        db_manager,
        wish_store,
        emby_client,
        security,
        tmdb_client,
        shadow_library,
        shadow_syncer,
        location_service,
        monitor,
        web_server,
    ):
        self.config = config
        self.db_manager = db_manager
        self.wish_store = wish_store
        self.emby_client = emby_client
        self.security = security
        self.tmdb_client = tmdb_client
        self.shadow_library = shadow_library
        self.shadow_syncer = shadow_syncer
        self.location_service = location_service
        self.monitor = monitor
        self.web_server = web_server

    def start(self):
        self.web_server.start()
        self.web_server.start_landing_posters_scheduler()
        self.monitor.run()


def create_app(config):
    db_manager = DatabaseManager(config['database']['name'])
    wish_store = WishStore(db_manager.db_path)
    emby_client = EmbyClient(server_url=config['emby']['server_url'], api_key=config['emby']['api_key'])
    security = EmbySecurity(emby_client)
    tmdb_client = TMDBClient(config.get('tmdb', {}))

    shadow_library = ShadowLibrary(db_manager.db_path)
    shadow_syncer = ShadowLibrarySyncer(emby_client, shadow_library)
    location_service = create_location_service(config, db_manager, emby_client)

    monitor = EmbyMonitor(
        db_manager=db_manager,
        emby_client=emby_client,
        security_client=security,
        config=config,
        location_service=location_service,
    )

    web_server = WebServer(
        db_manager=db_manager,
        emby_client=emby_client,
        security_client=security,
        config=config,
        location_service=location_service,
        monitor=monitor,
        tmdb_client=tmdb_client,
        wish_store=wish_store,
        shadow_library=shadow_library,
        shadow_syncer=shadow_syncer,
    )

    return EmbyQApp(
        config=config,
        db_manager=db_manager,
        wish_store=wish_store,
        emby_client=emby_client,
        security=security,
        tmdb_client=tmdb_client,
        shadow_library=shadow_library,
        shadow_syncer=shadow_syncer,
        location_service=location_service,
        monitor=monitor,
        web_server=web_server,
    )
