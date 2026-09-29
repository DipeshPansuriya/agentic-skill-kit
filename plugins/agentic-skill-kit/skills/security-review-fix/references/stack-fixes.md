# Vulnerable → Secure Patterns by Stack

Minimal-diff fixes. Keep behaviour for valid input identical; add a test that proves the malicious input is handled safely.

## .NET (C#, ASP.NET Core, EF Core)
| Issue (CWE) | Vulnerable | Secure |
|---|---|---|
| SQL injection (89) | `new SqlCommand("... WHERE Number = '" + awb + "'")` | `new SqlCommand("... WHERE Number = @awb", conn); cmd.Parameters.Add("@awb", SqlDbType.VarChar, 12).Value = awb;` |
| EF raw SQL (89) | `db.Awbs.FromSqlRaw($"... = '{awb}'")` | `db.Awbs.FromSql($"... = {awb}")` (EF 7+ parameterizes interpolation) or `FromSqlRaw("... = {0}", awb)` |
| IDOR (639) | `db.Awbs.FindAsync(id)` | `db.Awbs.SingleOrDefaultAsync(a => a.Id == id && a.TenantId == tenantId)` with `tenantId` from claims; 404 if null |
| Missing authz (862) | Controller without attributes | Global `FallbackPolicy = RequireAuthenticatedUser()`; `[Authorize(Policy = "CanEditAwb")]`; `[AllowAnonymous]` only where intended |
| Deserialization (502) | `BinaryFormatter`, `TypeNameHandling.All` | `System.Text.Json` with concrete types (BinaryFormatter is removed in .NET 9) |
| JWT (347) | `ValidateIssuer = false`, `ValidateLifetime = false`, `RequireSignedTokens = false` | All `Validate*` true, explicit `ValidIssuer`, `ValidAudience`, `ValidAlgorithms = ["RS256"]`, small `ClockSkew` |
| Password hash (916) | `MD5.HashData(...)` | `PasswordHasher<T>` (PBKDF2) or Argon2id library |
| Random token (338) | `new Random().Next()` | `RandomNumberGenerator.GetBytes(32)` → `Convert.ToHexString` / Base64Url |
| TLS (295) | `ServerCertificateCustomValidationCallback = (...) => true` | Remove; add the partner CA to the trust store or validate a pinned thumbprint for that host only |
| Path traversal (22) | `File.ReadAllBytes(Path.Combine(root, name))` | `var full = Path.GetFullPath(Path.Combine(root, name)); if (!full.StartsWith(rootFull + Path.DirectorySeparatorChar)) return BadRequest();` |
| CSRF (352) | Cookie auth + form POST without antiforgery | `[ValidateAntiForgeryToken]` / `AddAntiforgery` + `app.UseAntiforgery()`; SameSite=Lax/Strict cookies |
| XXE (611) | `XmlDocument` with `XmlResolver` set (old .NET Framework) | .NET Core defaults are safe; set `DtdProcessing = Prohibit`, `XmlResolver = null` explicitly for Cargo-XML parsing |

## Java (Spring Boot 3)
| Issue (CWE) | Vulnerable | Secure |
|---|---|---|
| SQL injection (89) | `jdbcTemplate.query("... hawb = '" + hawb + "'", m)` | `jdbcTemplate.query("... hawb = ?", m, hawb)` or `NamedParameterJdbcTemplate` |
| JPQL injection (89) | `em.createQuery("... where h = '" + h + "'")` | `em.createQuery("... where h = :h").setParameter("h", h)`; Spring Data derived queries |
| Sort/column injection (89) | `"ORDER BY " + sortField` | Map user choice to an allow-list: `Map.of("date", "created_at")` |
| Deserialization (502) | `new ObjectInputStream(in).readObject()`, Jackson `enableDefaultTyping()` | JSON to concrete DTO; if unavoidable: `ObjectInputFilter` allow-list |
| Authz (862/639) | Endpoint without method security | `@EnableMethodSecurity` + `@PreAuthorize("hasRole('AGENT')")`; tenant check in the repository query |
| CSRF (352) | `http.csrf(c -> c.disable())` on cookie-session app | Keep CSRF for browser sessions; disable only for stateless bearer-token APIs |
| Password hash (916) | `MessageDigest.getInstance("SHA-1")` | `PasswordEncoderFactories.createDelegatingPasswordEncoder()` (bcrypt) or `Argon2PasswordEncoder` |
| Random (338) | `new Random()` for OTP | `SecureRandom` |
| XXE (611) | `DocumentBuilderFactory.newInstance()` defaults | `dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)` |
| SSRF (918) | `restClient.get().uri(userUrl)` | Allow-list host + scheme; resolve and reject private/loopback/link-local IPs; disable redirects |
| Actuator (200) | `management.endpoints.web.exposure.include=*` | Expose `health,info` only; secure the rest behind admin role/port |

## Python (FastAPI / Django)
| Issue (CWE) | Vulnerable | Secure |
|---|---|---|
| SQL injection (89) | `cur.execute(f"... = '{awb}'")` | `cur.execute("... = %s", (awb,))`; SQLAlchemy `text("... = :awb")`, `{"awb": awb}` |
| Django raw (89) | `Model.objects.raw("... %s" % x)`, `.extra(where=[...])` | ORM filters, or `raw("... %s", [x])` |
| NoSQL injection (943) | `db.users.find({"user": req.json["user"]})` where value may be a dict (`{"$ne": null}`) | Validate type with Pydantic (`user: str`); reject operators |
| Command injection (78) | `subprocess.run(f"zip {name}", shell=True)` | `subprocess.run(["zip", name], check=True)` (no shell) |
| Deserialization (502) | `pickle.loads(data)`, `yaml.load(s)` | `json.loads`, `yaml.safe_load` |
| eval (95) | `eval(expr)` | `ast.literal_eval` for literals, or a dedicated parser |
| TLS (295) | `requests.get(url, verify=False)` | `verify="/path/ca-bundle.pem"` |
| Random (338) | `random.choices(...)` for tokens | `secrets.token_urlsafe(32)` |
| Password hash (916) | `hashlib.md5(pw)` | `argon2-cffi` `PasswordHasher`, Django default PBKDF2/Argon2 hasher |
| Path traversal (22) | `open(os.path.join(BASE, name))` | `p = (BASE / name).resolve(); p.relative_to(BASE.resolve())` (raises if outside) |
| Debug (489) | `DEBUG = True`, `app.run(debug=True)` | From env, default False; `ALLOWED_HOSTS` set |
| JWT (347) | `jwt.decode(t, options={"verify_signature": False})` | `jwt.decode(t, key, algorithms=["RS256"], audience=..., issuer=...)` |

## React
| Issue (CWE) | Vulnerable | Secure |
|---|---|---|
| XSS (79) | `<div dangerouslySetInnerHTML={{ __html: remarks }} />` | `<div>{remarks}</div>`; if HTML required: `DOMPurify.sanitize(remarks)` |
| URL XSS (79) | `<a href={userUrl}>` (allows `javascript:`) | Validate scheme: `new URL(u).protocol` in `['https:', 'http:']` |
| Token storage | JWT in `localStorage` | HttpOnly, Secure, SameSite cookie via BFF, or in-memory token with short lifetime |
| Secrets in bundle (798) | `const API_KEY = "sk_live..."` / `VITE_SECRET` | Anything in the bundle is public: move calls needing secrets to the backend |
| eval (95) | `new Function(code)` | Remove; data-driven logic |

## Angular
| Issue (CWE) | Vulnerable | Secure |
|---|---|---|
| XSS (79) | `this.sanitizer.bypassSecurityTrustHtml(userHtml)` | `[innerHTML]="userHtml"` (Angular sanitizes) or text interpolation `{{ }}` |
| DOM XSS (79) | `el.nativeElement.innerHTML = value` | Template binding or `Renderer2.setProperty(el, 'textContent', value)` |
| CSRF (352) | Custom header missing with cookie auth | `provideHttpClient(withXsrfConfiguration({ cookieName, headerName }))` matching the backend |
| Template injection (94) | Building templates from user strings / JIT compile | AOT only; never compile user input |

## SQL (T-SQL / PostgreSQL)
| Issue (CWE) | Vulnerable | Secure |
|---|---|---|
| Dynamic SQL (89) | `EXEC('SELECT ... WHERE Awb = ''' + @awb + '''')` | `EXEC sp_executesql N'SELECT ... WHERE Awb = @awb', N'@awb varchar(12)', @awb = @awb` |
| Dynamic identifiers (89) | `'ORDER BY ' + @col` | Allow-list + `QUOTENAME(@col)` (T-SQL) / `format('%I', col)` (PostgreSQL) |
| PL/pgSQL (89) | `EXECUTE 'SELECT ... ' || p_awb` | `EXECUTE 'SELECT ... WHERE awb = $1' USING p_awb` |
| Excess privilege (250) | App connects as `sa` / `postgres` / `db_owner` | Least-privilege role: only needed schemas and verbs; separate migration account |
| Sensitive data (311) | Passport numbers in clear text columns | Column encryption (Always Encrypted / pgcrypto) or tokenization; masking for non-prod |
