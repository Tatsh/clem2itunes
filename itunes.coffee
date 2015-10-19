ObjC.import 'AppKit'
ObjC.import 'Foundation'
ObjC.import 'stdlib'


class FileNotFoundError extends Error


class iTunesNotRunningError extends Error


class iTunes
    finder: Application 'Finder'
    _library: null

    running: ->
        for app in ObjC.unwrap($.NSWorkspace.sharedWorkspace.runningApplications)
            if typeof app.bundleIdentifier.isEqualToString is 'undefined'
                continue
            if app.bundleIdentifier.isEqualToString 'com.apple.iTunes'
                return true

        return false

    constructor: ->
        Object.defineProperty this, 'itunes', {
            get: =>
                if @_itunes
                    return @_itunes

                if not @running()
                    $.NSWorkspace.sharedWorkspace.launchAppWithBundleIdentifierOptionsAdditionalEventParamDescriptorLaunchIdentifier(
                        'com.apple.iTunes',
                        $.NSWorkspaceLaunchAsync | $.NSWorkspaceLaunchAndHide,
                        $.NSAppleEventDescriptor.nullDescriptor,
                        null,
                    )
                    delay 3

                @_itunes = Application('iTunes')
                se = Application('System Events')
                proc = se.processes.byName 'iTunes'
                @_devicesMenuItems = proc.menuBars[0].menuBarItems.byName 'File'
                                         .menus[0].menuItems.byName 'Devices'
                                         .menus[0].menuItems()

                return @_itunes
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
                    return @itunes.currentTrack
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
        paths = (Path(x.url().replace(/^file\:\/\//, '')) for x in root.entireContents())
        @itunes.add paths, {to: @library}
        # Refresh all tracks in case some changes do not get detected
        for track in @library.tracks()
            @itunes.refresh(track)

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
