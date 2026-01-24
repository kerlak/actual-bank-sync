# Security Policy

## ⚠️ Important Security Considerations

### Credential Storage

**This application stores bank credentials in memory only:**
- ✅ Bank credentials are **never** written to disk
- ✅ Credentials are **cleared** on application restart
- ✅ No persistent credential storage
- ⚠️ Users must re-enter credentials after each restart

**For Actual Budget:**
- Server password is stored in memory only
- Encryption passwords are stored in memory only
- File/account mappings are stored in memory (not sensitive)

### Data Privacy

**Downloaded Bank Data:**
- Bank statements (Excel/CSV files) contain **sensitive financial data**
- Files are stored in `./downloads/` directory
- Files persist until manually deleted
- **Recommendation:** Delete downloaded files after successful sync
- **Recommendation:** Use encrypted filesystem for the downloads directory

**In Home Assistant:**
- If running as HA add-on, downloads are stored in `/share/banking-hub/`
- These files persist across container restarts
- Ensure Home Assistant has proper filesystem encryption

### Network Security

**SSL/TLS:**
- Actual Budget connections skip SSL verification (`cert=False`)
- This is necessary for self-signed certificates
- ⚠️ Vulnerable to man-in-the-middle attacks on untrusted networks
- **Recommendation:** Use trusted network (VPN, local network only)

**Bank Connections:**
- Uses Playwright which validates bank SSL certificates
- Bank traffic is properly encrypted via HTTPS

### Code Security

**No Hardcoded Secrets:**
- ✅ No API keys, passwords, or tokens in source code
- ✅ All sensitive config via environment variables
- ✅ Sample configs use placeholder values only

**Dependencies:**
- Uses `actualpy`, `playwright`, `pywebio`, `pandas`
- **Recommendation:** Run `pip list --outdated` periodically
- **Recommendation:** Update dependencies for security patches

## 🔒 Best Practices for Users

### Before Running

1. **Review the code**: Understand what the application does
2. **Use dedicated environment**: Don't run on systems with other sensitive data
3. **Use encrypted filesystem**: Enable filesystem encryption (LUKS, FileVault, BitLocker)
4. **Restrict network access**: Run on trusted network only

### During Operation

1. **Clear downloads regularly**: Delete CSV/Excel files after sync
2. **Monitor logs**: Check for unusual activity
3. **Use strong passwords**: For Actual Budget server
4. **Restart to clear memory**: Restart container to clear credentials from memory

### For Self-Hosting

1. **Use firewall**: Restrict port 2077 to local network only
2. **Use reverse proxy**: Add authentication layer (nginx, Traefik)
3. **Use VPN**: Access via VPN for remote connections
4. **Regular backups**: Backup Actual Budget data separately
5. **Update regularly**: Pull latest version for security fixes

## ⚖️ Legal and Terms of Service Considerations

### Bank Scraping

**⚠️ IMPORTANT DISCLAIMER:**

This software automates the download of bank statements from Spanish banks (Ibercaja, ING) using web scraping techniques. **Be aware of the following:**

#### Legal Considerations

1. **Terms of Service**: Automated access may violate the banks' Terms of Service
2. **PSD2 Compliance**: EU Payment Services Directive 2 (PSD2) grants users the right to access their own financial data, but banks may require specific methods (APIs)
3. **Personal Use Only**: This tool is intended for personal use only with your own accounts
4. **No Warranty**: This software is provided "AS IS" without warranty of any kind

#### Risks

- **Account Suspension**: Banks may suspend accounts for automated access
- **Legal Action**: Banks may take legal action for ToS violations
- **Liability**: The maintainers are not responsible for any consequences

#### Recommendations

1. **Check ToS**: Read your bank's Terms of Service regarding automated access
2. **Use Official APIs**: Prefer official bank APIs when available
3. **Manual Download**: Consider manually downloading files instead
4. **Consent**: Only use with accounts you own or have explicit permission to access
5. **Jurisdiction**: Understand laws in your jurisdiction regarding web scraping

#### Alternative: Manual Upload

To avoid automated scraping:
- Download Excel files manually from your bank's website
- Use the `[upload xlsx]` feature in the web UI
- This approach doesn't violate automation restrictions

## 🐛 Reporting Security Issues

**Do NOT open public GitHub issues for security vulnerabilities.**

Instead:
1. Check if issue already exists in closed issues
2. If new, contact repository maintainer directly
3. Provide detailed description of vulnerability
4. Allow time for fix before public disclosure

## 📋 Security Checklist Before Going Public

### Repository Audit

- [ ] No credentials in git history
- [ ] No sensitive data in any commit
- [ ] `.gitignore` properly configured
- [ ] All hardcoded configs removed
- [ ] Sample configs use placeholders only

### Documentation

- [ ] Security policy documented (this file)
- [ ] Legal disclaimers added
- [ ] Installation instructions include security best practices
- [ ] User warnings about ToS violations

### Code Review

- [ ] No SQL injection vulnerabilities
- [ ] No command injection vulnerabilities
- [ ] No path traversal vulnerabilities
- [ ] Input validation on all user inputs
- [ ] Proper error handling (no sensitive data in errors)

### License

- [ ] Choose appropriate license (MIT, GPL, etc.)
- [ ] Include disclaimer of warranty
- [ ] Include limitation of liability

## 📜 License and Liability

**This software is provided for educational and personal use only.**

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

**Users assume all risks and responsibilities for:**
- Compliance with bank Terms of Service
- Compliance with local laws and regulations
- Security of their own credentials and data
- Any consequences of using this software

## 🔄 Version History

- **v1.1.0**: Added per-file encryption, saved mappings, credential management
- **v1.0.0**: Initial public release

## 📞 Contact

For security concerns, contact the repository maintainer through GitHub.
