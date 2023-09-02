import { FILE_URI_PREFIX_RE } from './constants';

const lawbio = 'launchAppWithBundleIdentifierOptionsAdditionalEventParamDescriptorLaunchIdentifier';

export default class ITunes {
  private pDevicesMenuItems: Entries<MenuItem>;
  private pItunes: ITunesApplication;
  private pLibrary: ITunesLibrary;
  finder = Application('Finder');

  running(): boolean {
    for (const app of ObjC.unwrap($.NSWorkspace.sharedWorkspace.runningApplications)) {
      if (
        typeof app.bundleIdentifier.isEqualToString !== 'undefined' &&
        app.bundleIdentifier.isEqualToString('com.apple.iTunes')
      ) {
        return true;
      }
    }
    return false;
  }

  get itunes(): ITunesApplication {
    if (this.pItunes) {
      return this.pItunes;
    }
    if (!this.running()) {
      $.NSWorkspace.sharedWorkspace[lawbio](
        'com.apple.iTunes',
        $.NSWorkspaceLaunchAsync | $.NSWorkspaceLaunchAndHide,
        $.NSAppleEventDescriptor.nullDescriptor,
        null,
      );
      delay(3);
    }
    this.pItunes = Application('iTunes');
    const se = Application('System Events');
    const proc = se.processes.byName('iTunes');
    this.pDevicesMenuItems = proc.menuBars[0].menuBarItems
      .byName('File')
      .menus[0].menuItems.byName('Devices')
      .menus[0].menuItems();
    return this.pItunes;
  }

  get library(): ITunesLibrary {
    if (this.pLibrary) {
      return this.pLibrary;
    }
    for (const source of this.itunes.sources()) {
      if (source.name() === 'Library') {
        this.pLibrary = source as ITunesLibrary;
        break;
      }
    }
    return this.pLibrary;
  }

  get currentTrack(): ITunesTrack | null {
    try {
      return this.itunes.currentTrack;
    } catch (e) {
      return null;
    }
  }

  deleteOrphanedTracks(): any[] {
    const ret = [];
    for (const track of this.library.tracks()) {
      const name = track.name();
      let loc;
      try {
        loc = track.location();
      } catch (e) {
        console.debug(`Removing ${name}`);
        ret.push(track);
        track.delete();
        continue;
      }
      if (!loc || !this.finder.exists(loc)) {
        console.debug(`Removing ${name}`);
        ret.push(track);
        track.delete();
      }
    }
    return ret;
  }

  /**
   * Root must be a Finder folder item
   * `finder.home().folders.byName('Music').folders.byName('import');`
   */
  addTracksAtPath(root: FinderFolderItem): string[] {
    const paths = root.entireContents().map((x) => Path(x.url().replace(FILE_URI_PREFIX_RE, '')));
    this.itunes.add(paths, {
      to: this.library,
    });
    // Refresh all tracks in case some changes do not get detected
    const results = [];
    for (const track of this.library.tracks()) {
      results.push(this.itunes.refresh(track));
    }
    return results;
  }

  private clickDevicesMenuItem(regex: RegExp): boolean {
    this.itunes.activate();
    for (let i = 0; i < this.pDevicesMenuItems.length; i++) {
      const item = this.pDevicesMenuItems[i];
      if (regex.test(item.title()) && item.enabled()) {
        item.click();
        return true;
      }
    }
    return false;
  }

  syncDevice(): boolean {
    return this.clickDevicesMenuItem(/^Sync /);
  }

  backupDevice(): boolean {
    return this.clickDevicesMenuItem(/^Back Up$/);
  }

  transferPurchasesFromDevice(): boolean {
    return this.clickDevicesMenuItem(/^Transfer Purchases from /);
  }
}
