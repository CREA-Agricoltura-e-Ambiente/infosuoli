# Snap! Media

Derived from `opengisch/qfield-snap` (GPL-2.0); everything here is under the same licence.

## Files
- `snap-media-plugin.zip` – QField plugin (`main.qml` + `metadata.txt`)
- `make_media_gpkg.py` – creates `media.gpkg`, registers photo/audio/raster files from a folder
- `classify_media.py` – labels photos as `soilprofile` / `soilsite` with CLIP

## media.gpkg (table `media`, points, EPSG:4326)
Identifier columns follow the SoilWise GeoPackage for INSPIRE Soil
(https://soilwise-he.github.io/Geopackage-so/):

| column | notes |
|---|---|
| `inspireid_namespace` | TEXT(20), set once per project |
| `inspireid_localid` | TEXT(14), `YYYYMMDDHHMMSS`, unique within the namespace (unique index) |
| `inspireid_versionid` | optional |
| `mediatype` | `photo` / `audio` / `raster` |
| `subject` | `soilprofile` / `soilsite` / `to_verify` (NULL = not classified) |
| `path` | relative to the gpkg, e.g. `DCIM/soilprofile/20261118105100.jpg` |
| `name`, `captured_at`, `azimuth`, `mime`, `author`, `notes`, `ai_confidence` | |
| `relatedguid` | guid of the SoilProfile / SoilSite record the media documents (optional) |

## Setup
1. `python make_media_gpkg.py init media.gpkg`
2. QGIS → layer `media` → Properties → Attributes Form:
   - `path`: **Attachment** widget, path relative to the project (works for photo, audio, raster)
   - `mediatype`, `subject`: **Value Map**
   - `inspireid_namespace`, `inspireid_localid`: read-only (the plugin fills them)
   - `notes`: text edit (Vocal QField dictation goes here)
3. Save the project next to `media.gpkg`, package with QFieldSync / QFieldCloud.
4. Install `snap-media-plugin.zip` in QField (settings → plugin manager).

## In the field
- On project start a dialog asks for the **INSPIRE namespace** (max 20 chars: letters, digits `.` `_` `-`).
  It is stored per project on the device; change it from the menu → *INSPIRE namespace...*
- Select the `media` layer, tap the camera button and choose:
  *Photo - soil profile*, *Photo - soil site*, *Audio note*, *Raster map*.
- Each new record gets `inspireid_namespace` and `inspireid_localid` automatically. Photos are saved in
  `DCIM/soilprofile/` or `DCIM/soilsite/` and named `<localid>.<ext>`. For audio and raster the form opens
  with `mediatype` set: record or pick the file with the Attachment widget of `path`.

## Back at the desk
- Files that did not come from the plugin: `python make_media_gpkg.py ingest media.gpkg FOLDER --namespace IT.MYORG.SOIL`
  (FOLDER must be inside the gpkg folder; the localid comes from EXIF/file time, +1 s on collisions).
- `python classify_media.py media.gpkg --dry-run`, then without `--dry-run`.

## Known limits
- The QML plugin is untested on a device; the namespace dialog, the settings storage and the
  `loadProjectEnded` hook rely on QField APIs I could not run here. If the dialog does not appear at start,
  it appears on the first tap of the button.
- Two records in the same second would get the same localid: the unique index rejects the second one.
- Raster maps stay external files referenced by `path`.
