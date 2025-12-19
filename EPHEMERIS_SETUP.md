# Swiss Ephemeris Data Files — REQUIRED

## CRITICAL: The engine will NOT function without these files.

### Download Location
https://www.astro.com/ftp/swisseph/ephe/

### Required Files (place in `ephemeris_data/` directory)

#### Planetary Data (MANDATORY)
- `sepl_18.se1` — Main planets 1800-2400 AD
- `semo_18.se1` — Moon 1800-2400 AD  
- `seas_18.se1` — Asteroids (optional, for extended bodies)

#### Alternative: Shorter Range Files
- `sepl_*.se1` — Planets for specific century ranges
- `semo_*.se1` — Moon for specific century ranges

### Download Commands (Linux/Mac)
```bash
cd ephemeris_data
wget https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1
wget https://www.astro.com/ftp/swisseph/ephe/semo_18.se1
```

### Download Commands (Windows PowerShell)
```powershell
cd ephemeris_data
Invoke-WebRequest -Uri "https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1" -OutFile "sepl_18.se1"
Invoke-WebRequest -Uri "https://www.astro.com/ftp/swisseph/ephe/semo_18.se1" -OutFile "semo_18.se1"
```

### Verification
After downloading, the engine will validate file presence on startup.
If files are missing → **ENGINE WILL FAIL LOUD**.

### File Size Reference
- `sepl_18.se1` — ~1.4 MB
- `semo_18.se1` — ~13 MB

### Note on Moshier Ephemeris
If `.se1` files are not found, pyswisseph falls back to the built-in Moshier ephemeris.
Moshier is less precise (~1 arcsecond vs ~0.001 arcsecond for Swiss Ephemeris).
For production use, Swiss Ephemeris files are REQUIRED.
