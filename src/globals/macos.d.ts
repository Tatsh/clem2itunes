interface FinderFolderContentName {
  url: () => string;
}

interface FinderApplication {
  exists: (path: string) => boolean;
  home: () => FinderFolderItem;
}

interface Application {
  activate: () => void;
}

interface Path {
  a: any;
}

interface Entries<T> {
  (): Entries<T>;
  [n: number]: T;
  byName: (name: string) => T;
  length: number;
}

interface MenuItem {
  click: () => any;
  enabled: () => boolean;
  menus: Menu[];
  title: () => string;
}

interface Menu {
  menuItems: Entries<MenuItem>;
}

interface MenuBarItem {
  menus: Menu[];
}

interface MenuBar {
  menuBarItems: Entries<MenuBarItem>;
}

interface SystemEventsProcess {
  menuBars: MenuBar[];
}

interface SystemEventsApplication extends Application {
  processes: Entries<SystemEventsProcess>;
}

interface FinderItem {
  url: () => string;
}

interface FinderFolderItem {
  entireContents: () => FinderFolderContentName[];
  folders: Entries<FinderFolderItem>;
  items: Entries<FinderItem>;
}

interface NSString {
  isEqualToString: (value: string | NSString) => boolean;
  lastPathComponent: NSString;
}

interface NSObject {
  init: () => NSObject;
}

interface NSArray<T = any> extends NSObject {
  initWithArray: (array: NSArray<T>) => NSArray;
}

interface WorkspaceApplication {
  bundleIdentifier: Partial<NSString>;
}

declare const ObjC: {
  import: (name: string) => void;
  unwrap: <U>(value: U) => U extends NSString ? string : U extends NSArray<infer V> ? V[] : any;
};
declare const $: {
  NSAppleEventDescriptor: { nullDescriptor: any };
  NSString: {
    stringWithContentsOfFileUsedEncodingError: (
      path: NSString | string,
      encoding: number,
      unk: any,
    ) => NSString;
    stringWithString: (str: NSString | string) => NSString;
  };
  NSUTF8StringEncoding: number;
  NSWorkspace: {
    sharedWorkspace: {
      launchAppWithBundleIdentifierOptionsAdditionalEventParamDescriptorLaunchIdentifier: (
        name: string,
        flags: number,
        descriptor: any,
        unk: any,
      ) => void;
      runningApplications: NSArray<WorkspaceApplication>;
    };
  };
  NSWorkspaceLaunchAndHide: number;
  NSWorkspaceLaunchAsync: number;
  exit: (n: number) => never;
};
declare function Application(name: 'Finder'): FinderApplication;
declare function Application(name: 'System Events'): SystemEventsApplication;
declare function Application(name: 'iTunes'): ITunesApplication;
declare function Application(name: string): Application;
declare function Path(path: string): Path;
declare function delay(seconds: n): void;
