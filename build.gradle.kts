import myaa.subkt.ass.*
import myaa.subkt.tasks.*
import myaa.subkt.tasks.Mux.*
import myaa.subkt.tasks.Nyaa.*
import java.awt.Color
import java.time.*

plugins {
    id("myaa.subkt")
}

subs {
    readProperties("sub.properties", "private.properties")
    episodes(getList("episodes"))

    merge {
        from(get("dialogue")) {
            incrementLayer(10)
        }
        from(getList("typesets"))
        from(getList("opening"))
        from(getList("insert"))
        from(getList("ending"))

        includeExtraData(false)
        includeProjectGarbage(false)
    }

    swap {
        from(merge.item())
    }

    mux {
        title(get("title"))

        from(get("premux")) {
            includeChapters(false)

            video {
                name("BD 1080p HEVC [dedsec]")
                lang("jpn")
                default(true)
            }

            audio(0) {
                name("Japanese 5.1 AAC")
                lang("jpn")
                default(true)
            }

            audio(1) {
                name("Japanese 2.0 AAC")
                lang("jpn")
            }

            attachments {
                include(false)
            }
        }

        from(merge.item()) {
            tracks {
                name("Kaizoku")
                lang("eng")
                default(true)
            }
        }

        from(swap.item()) {
            tracks {
                name("Kaizoku (Honorifics)")
                lang("enm")
            }
        }

        chapters(get("chapters")) {
            lang("eng")
            charset("UTF-8")
        }

        attach(get("fonts")) {
            includeExtensions("ttf", "otf")
        }

        skipUnusedFonts(true)
        forceCRC("00000000")
        out(get("muxfile"))
    }

    torrent {
        trackers(getList("tracker"))
        from(mux.item())
        out(get("torrent"))
    }

    nyaa {
        from(torrent.item())
        username(get("nyaauser"))
        password(get("nyaapass"))
        category(NyaaCategories.ANIME_ENGLISH)
        information(get("gitrepo"))
        torrentDescription(getFile("description.vm"))
        hidden(false)
    }
}
