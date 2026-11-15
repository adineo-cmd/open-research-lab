# format-re-targets — 21 sources

| source | what you can do there | agent access | tier | url check |
|---|---|---|---|---|
| [ArchiveTeam](https://www.archiveteam.org) | Volunteer archivist collective (warrior client) — join preservation campaigns. | Archiving warrior + wiki. | curated | ok |
| [dexvert samples](https://github.com/Sembiance/dexvert) | The dexvert project's massive sample-file corpus per format — RE fuel. | git clone. | curated | ok |
| [digipres.org](https://digipres.org) | Aggregated view of digital-preservation data: PRONOM, format registries and tool registries in one place. | Scrape its aggregated registries for cross-registry format comparisons. | curated | redirect-ok |
| [discmaster](https://discmaster.textfiles.com) | Search engine over 5000+ archive.org CD-ROM/DVD images — find rare binaries/samples. | Browse; item-level extraction via archive.org. | curated | ok |
| [file / libmagic (magic number database)](https://github.com/file/file) | The classic file(1) utility source with the magic-number database used system-wide for format identification. | Compile/inspect the magic database to map signatures to formats programmatically. | curated | 200 |
| [fileinfo.com](https://fileinfo.com) | Per-extension database with links to programs/specs. | Browse. | curated | ok |
| [Gary Kessler file signature table](https://www.garykessler.net/library/file_sigs.html) | Widely-referenced hex-signature table mapping file headers to formats for forensics and identification. | Scrape the HTML table into a magic-bytes lookup for file triage. | curated | 200 |
| [Ghidra](https://ghidra-sre.org) | NSA's open-source reverse-engineering framework with disassembly, decompilation and scripting for 50+ formats. | Run headless analysis (analyzeHeadless) to decompile binaries programmatically. | curated | redirect-ok |
| [GitHub Archive](https://www.gharchive.org) | Every public GitHub event since 2011 (hourly JSON). | BigQuery + S3 bulk. | curated | ok |
| [ImHex](https://github.com/WerWolv/ImHex) | Hex editor with a pattern-language for structurally parsing binary formats and data visualization. | Use .hexpat pattern files to parse unknown binary structures; headless scripting available. | curated | 200 |
| [Internet Archive software collection](https://archive.org/details/software) | Emulated + raw software images spanning decades. | Item REST API. | curated | ok |
| [Just Solve It (File Format Wiki)](https://justsolve.archiving.it) | ArchiveTeam-hosted wiki cataloging thousands of file formats with identification and extraction hints. | Scrape MediaWiki API (api.php) for format pages and extension mappings. | curated | dead |
| [LoC Sustainability of Digital Formats](https://www.loc.gov/preservation/digital/formats) | Library of Congress format descriptions (FDD) with identification, encoding and sustainability notes. | Scrape the format-description pages for canonical format metadata. | curated | redirect-ok |
| [Open Preservation Foundation](https://www.openpreservation.org) | Non-profit maintaining open preservation tools (veraPDF, JHOVE, Tika fork) and format knowledge. | Fetch their open-source tooling releases for file validation pipelines. | curated | redirect-ok |
| [PRONOM (TNA file format registry)](https://www.nationalarchives.gov.uk/PRONOM) | UK National Archives' technical registry of file formats (PUIDs) with signatures and version info. | Query the PRONOM web services (REST/SOAP) for format PUIDs and signatures. | curated | redirect-ok |
| [radare2](https://github.com/radareorg/radare2) | Scriptable RE framework for disassembly, binary analysis and forensics across architectures. | Drive r2 via r2pipe JSON commands for automated binary analysis. | curated | 200 |
| [sembiance fileFormatSamples](https://www.sembiance.com/fileFormatSamples) | Mark Biesheuvel's per-format sample corpus (used by dexvert) — RE fuel. | Direct download per format. | curated | network-error (host known-live; re-verify — session network degradation) |
| [Software Heritage](https://www.softwareheritage.org) | Universal source-code archive (graph of all known VCS history). | API + graph dataset. | curated | ok |
| [textfiles.com](https://www.textfiles.com) | Jason Scott's classic BBS-era text-file archive (magazines, hacker docs, art packs) plus upload history. | Scrape directory listings for bulk corpus of early-digital ephemera. | curated | error (kept+flagged) |
| [Wikipedia file-format list](https://en.wikipedia.org/wiki/List_of_file_formats) | Index of hundreds of formats incl. obscure ones. | MediaWiki API. | curated | ok |
| [YARA](https://github.com/VirusTotal/yara) | Pattern-matching engine for classifying files by rules - standard tool for malware and format triage. | Write YARA rules and run yarac/yara CLI over sample corpora for detection tasks. | curated | 200 |
