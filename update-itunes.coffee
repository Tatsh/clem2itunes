ObjC.import 'AppKit'
ObjC.import 'Foundation'


class FileNotFoundError extends Error


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
                if @_itunes
                    return @_itunes

                if not @running()
                    $.NSWorkspace.sharedWorkspace.launchAppWithBundleIdentifierOptionsAdditionalEventParamDescriptorLaunchIdentifier(
                        'com.apple.iTunes',
                        $.NSWorkspaceLaunchAsync | $.NSWorkspaceLaunchAndHide,
                        $.NSAppleEventDescriptor.nullDescriptor,
                        null,
                    )
                    @_itunes = Application('iTunes')

                return @_itunes
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


it = new iTunes()
dir = it.finder.home().folders.byName('Music').folders.byName('import')

console.log 'Deleting orphaned tracks'
deleted = it.deleteOrphanedTracks()

console.log 'Updating iTunes track list'
it.addTracksAtPath dir

# Update ratings
# Have to use .items for 'hidden' files
filePath = dir.items.byName('.ratings').url().replace(/^file\:\/\//, '')
ratingsFileData = $.NSString.stringWithContentsOfFileUsedEncodingError(filePath, $.NSUTF8StringEncoding, null)
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
