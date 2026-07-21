# Apple Daily ninjs format migration

The extraction and archive organizer use the project form based on **ninjs
3.2**.  It follows the supplied example and deliberately emits a small,
consistent subset of the full IPTC schema.

## Former form versus new form

| Concern | Former archive (ninjs 2.1-style) | New project form (ninjs 3.2) |
|---|---|---|
| Standard | `version: "2.1"` | `version: "3.2"` |
| Property naming | lowercase, e.g. `firstcreated` | camelCase, e.g. `firstCreated` |
| Alternative IDs | `altids` | `altIds` |
| Body MIME type | absent or `contenttype` | `contentType: "text/plain"` |
| Article with photos | `type: "text"` | `type: "composite"`, `profile: "text-photo"` |
| Article without photos | `type: "text"` | `type: "text"`, with no `profile` |
| Picture association | could include local `renditions` | `name`, original `uri`, `type`, optional caption `headlines` |
| Dates | often date-only (`YYYY-MM-DD`) | evidenced ISO 8601 date-time with timezone |
| URI | could retain query/fragment | canonical article URI without query/fragment |
| Credit in body | extraction could remove it | retained in `bodies`; also parsed into `by` and `located` |

Date-only legacy values are useful for directory placement, but they are not
invented as midnight timestamps.  If an exact time and timezone cannot be
recovered, the converter omits that optional ninjs date property.  Current
WARC extraction recovers `firstCreated` from page metadata and
`versionCreated` from `WARC-Date`.

## Canonical property order

Records are written in this readable order:

1. `uri`, `standard`
2. evidenced `firstCreated`, `versionCreated`, `contentCreated`
3. `type` and optional `profile`
4. `language`, `headlines`, `subjects`, `bodies`, `associations`
5. `by`, `located`, `altIds`

JSON object order has no semantic meaning, but keeping it stable makes review
and diffs substantially easier.
