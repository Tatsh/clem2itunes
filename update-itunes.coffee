ObjC.import 'AppKit'
ObjC.import 'Foundation'
ObjC.import 'stdlib'

lawbio = "launchAppWithBundleIdentifierOptionsAdditionalEventParam\
          DescriptorLaunchIdentifier"


class FileNotFoundError extends Error


class iTunesNotRunningError extends Error


class iTunes
    finder: Application 'Finder'
    _library: null

    running: ->
        apps = ObjC.unwrap($.NSWorkspace.sharedWorkspace.runningApplications)
        ret = false
        for app in apps
            if typeof app.bundleIdentifier.isEqualToString is 'undefined'
                continue
            if app.bundleIdentifier.isEqualToString 'com.apple.iTunes'
                ret = true
                break
        ret

    constructor: ->
        Object.defineProperty this, 'itunes', {
            get: =>
                if @_itunes
                    return @_itunes

                if not @running()
                    $.NSWorkspace.sharedWorkspace[lawbio](
                        'com.apple.iTunes',
                        $.NSWorkspaceLaunchAsync | $.NSWorkspaceLaunchAndHide,
                        $.NSAppleEventDescriptor.nullDescriptor,
                        null,
                    )
                    delay 3

                @_itunes = Application('iTunes')
                se = Application('System Events')
                proc = se.processes.byName 'iTunes'
                @_devicesMenuItems = proc.menuBars[0]
                                         .menuBarItems.byName 'File'
                                         .menus[0].menuItems.byName 'Devices'
                                         .menus[0].menuItems()

                @_itunes
        }
        Object.defineProperty this, 'library', {
            get: =>
                if @_library
                    return @_library

                for source in @itunes['sources']()
                    if source.name() is 'Library'
                        @_library = source
                        break

                @_library
        }
        Object.defineProperty this, 'currentTrack', {
            get: =>
                try
                    @itunes.currentTrack
                catch
                    null
        }

    deleteOrphanedTracks: ->
        ret = []
        for track in @library.tracks()
            name = track.name()
            try
                loc = track.location()
            catch
                console.log "Removing #{ name }"
                ret.push track
                track.delete()
                continue

            if not loc or not @finder.exists loc
                console.log "Removing #{ name }"
                ret.push track
                track.delete()

        ret

    # root must be a Finder folder item
    # finder.home().folders.byName('Music').folders.byName('import');
    addTracksAtPath: (root) ->
        paths = root.entireContents().map(
            () -> Path(x.url().replace(/^file\:\/\//, '')))
        @itunes.add paths, {to: @library}
        # Refresh all tracks in case some changes do not get detected
        for track in @library.tracks()
            @itunes.refresh track

    _clickDevicesMenuItem: (regex) ->
        @itunes.activate()
        for item in @_devicesMenuItems
            if regex.test(item.title()) and item.enabled()
                item.click()

    syncDevice: ->
        @_clickDevicesMenuItem /^Sync /

    backupDevice: ->
        @_clickDevicesMenuItem /^Back Up$/

    transferPurchasesFromDevice: ->
        @_clickDevicesMenuItem /^Transfer Purchases from /


it = new iTunes()
dir = it.finder.home().folders.byName('Music').folders.byName('import')

console.log 'Deleting orphaned tracks'
deleted = it.deleteOrphanedTracks()

console.log 'Updating iTunes track list'
it.addTracksAtPath dir

# Update ratings
# Have to use .items for 'hidden' files
filePath = dir.items.byName('.ratings').url().replace(/^file\:\/\//, '')
ratingsFileData = $.NSString.stringWithContentsOfFileUsedEncodingError(
    filePath, $.NSUTF8StringEncoding, null)
ratings = {}

console.log 'Building basename:track hash'
for track in it.library.tracks()
    loc = track.location().toString()
    loc = ObjC.unwrap($.NSString.stringWithString(loc).lastPathComponent)
    ratings[loc] = track

console.log 'Setting ratings'
for line in ObjC.unwrap(ratingsFileData).split '\n'
    line = line.trim()

    if not line
        continue

    [rating, filename] = line.split ' '
    filename = filename.trim()
    rating = (parseInt(rating, 10) / 5) * 100

    if filename not of ratings
        throw new FileNotFoundError filename

    ratings[filename]().rating = rating

console.log 'Syncing device if present'
try
    it.syncDevice()
catch
    # Nothing

$.exit 0
