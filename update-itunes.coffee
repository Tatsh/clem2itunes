ObjC.import 'stdio'
ObjC.import 'AppKit'


class iTunesNotRunningError extends Error


class iTunes
    finder: Application 'Finder'
    _library: null

    running: ->
        for app in ObjC.unwrap($.NSWorkspace.sharedWorkspace.runningApplications)
            if typeof app.bundleIdentifier.isEqualToString == 'undefined'
                continue
            if app.bundleIdentifier.isEqualToString 'com.apple.iTunes'
                return true

        return false

    constructor: ->
        Object.defineProperty this, 'itunes', {
            get: =>
                if not @running()
                    throw new iTunesNotRunningError('iTunes not found to be running')

                return Application('iTunes')
        }
        Object.defineProperty this, 'library', {
            get: =>
                if @_library
                    return @_library

                for source in @itunes['sources']()
                    if source.name() == 'Library'
                        @_library = source
                        break

                @_library
        }
        Object.defineProperty this, 'currentTrack', {
            get: =>
                @itunes.currentTrack
        }

    clearOrphanedTracks: ->
        ret = []
        for track in @library.tracks()
            name = track.name()
            try
                loc = track.location()
            catch
                $.printf "Removing #{ name }"
                ret.push track
                track.delete()
                continue

            if not loc or not @finder.exists loc
                $.printf "Removing #{ name }"
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


it = new iTunes()
it.itunes
