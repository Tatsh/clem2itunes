interface ITunesSource {
  name: () => string;
}

interface ITunesApplication extends Application {
  add: (paths: Path[], args: { to: ITunesSource }) => void;
  currentTrack: ITunesTrack | null;
  refresh: (track: ITunesTrack) => string;
  sources: () => ITunesSource[];
}

interface ITunesTrack {
  (): { rating: number };
  delete: () => void;
  location: () => string;
  name: () => string;
}

interface ITunesLibrary extends ITunesSource {
  tracks: () => ITunesTrack[];
}
