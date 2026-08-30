# Research and novelty boundary

Research was refreshed on 2026-08-30 before MarkerWalk 0.1.0 was built. The claim here is narrow:
MarkerWalk addresses a workflow gap found during public-source research; it does not claim that no
one has ever written similar private or unindexed software.

## Adjacent products

- [BillionGraves](https://support.billiongraves.com/support/solutions/articles/35000113634-how-does-billiongraves-work-)
  focuses on GPS-tagged capture, upload, transcription, and linking multiple images to a record.
- [Find a Grave](https://news.findagrave.com/2025/05/15/find-photo-requests-near-you/)
  provides nearby photo-request lists and maps inside its network.
- [Sunrise CMS](https://github.com/cityssm/sunrise-cms) is cemetery-management software for records,
  maps, work orders, and public search.

Those are useful systems, but they are not MarkerWalk's authority. MarkerWalk takes an explicit
local manifest and answers a smaller evidence question before upload: which required views are
backed by existing files, which declared files are missing, which local images are unreferenced,
what prior attempts should remain visible, and what deterministic revisit packet follows from the
gaps.

## Repository and name search

GitHub repository searches for the exact name `MarkerWalk` and combinations of cemetery/grave
photo audit, missing-view coverage, and revisit routing did not reveal a focused equivalent during
the research window. Broader searches found platform clients, cemetery databases, mapping tools,
and general duplicate-photo utilities. They were treated as adjacent rather than proof of global
uniqueness.

## Deliberate non-overlap

MarkerWalk does not provide cemetery record management, public memorial pages, crowdsourced
requests, GPS capture, EXIF extraction, image recognition, transcription, duplicate-image hashing,
upload, accounts, or a hosted map. Adding any of those would require a new problem statement and
another overlap review.
