# Security Guidelines for TinyTroupe

## Overview

This document provides security guidelines and best practices for using and developing with TinyTroupe. Following these guidelines helps ensure safe operation and protects against potential security vulnerabilities.

## API Key and Credential Security

### Environment Variables
✅ **DO**: Store API keys in environment variables
```bash
export OPENAI_API_KEY="sk-your-actual-key-here"
export AZURE_OPENAI_API_KEY="your-azure-key-here"
```

❌ **DON'T**: Hard-code API keys in source code
```python
# NEVER do this
openai_api_key = "sk-1234567890abcdef"
```

### API Key Validation
- API keys must be at least 10 characters long
- Avoid obvious dummy values like "dummy", "test", "example"
- Use different API keys for development and production
- Rotate API keys regularly

### Endpoint Security
- Always use HTTPS endpoints for API communications
- Validate endpoint URLs to prevent redirect attacks
- Use official Azure OpenAI endpoints only

## Input Validation and Sanitization

### JSON Processing Security
The improved `extract_json` function includes several security measures:

```python
# Size limits to prevent DoS attacks
MAX_INPUT_SIZE = 1_000_000  # 1MB limit

# Depth checking to prevent stack overflow
def check_depth(obj, max_depth=50):
    # Prevents deeply nested JSON attacks
```

### User Input Handling
- Validate all user inputs before processing
- Sanitize file paths to prevent directory traversal
- Limit input sizes to reasonable bounds
- Use allowlists for acceptable input patterns

### LLM Output Processing
- Never execute LLM outputs as code
- Validate JSON structures before parsing
- Implement rate limiting for LLM requests
- Log suspicious or malformed outputs

## Configuration Security

### Configuration File Protection
```ini
# config.ini - Use secure values
[OpenAI]
API_TYPE=openai
CACHE_API_CALLS=False  # Be cautious with caching sensitive data
MAX_CONTENT_DISPLAY_LENGTH=1000  # Limit output size
```

### Dangerous Configuration Patterns
❌ **Avoid**:
- Storing credentials in configuration files
- Using `eval()` or `exec()` with configuration values
- Allowing arbitrary file paths in configuration
- Enabling debug modes in production

### Configuration Validation
The new validation system checks for:
- Valid API types and model names
- Reasonable parameter ranges
- Safe file paths and URLs
- Proper endpoint formats

## Memory and Resource Security

### Memory Management
- Set maximum memory limits for agent storage
- Implement automatic cleanup of old data
- Monitor memory usage in long-running simulations
- Use bounded data structures where possible

### Prevent Resource Exhaustion
```python
# Example: Limit agent action loops
MAX_ACTIONS_BEFORE_DONE = 15
LOOP_DETECTION_THRESHOLD = 5

# Example: Limit memory growth
MAX_EPISODIC_MEMORIES = 1000
MAX_SEMANTIC_DOCUMENTS = 5000
```

## Error Handling Security

### Information Disclosure Prevention
```python
# Good: Generic error messages for users
try:
    result = process_user_input(input_data)
except Exception:
    logger.error("Processing failed", exc_info=True)  # Log details
    return {"error": "Processing failed"}  # Generic user message
```

### Secure Error Context
```python
# Use the custom exception system
from tinytroupe.exceptions import ValidationError, create_error_context

try:
    validate_input(user_data)
except ValidationError as e:
    context = create_error_context(additional_info="user_input_validation")
    handle_error_with_context(e, context, logger)
```

## Simulation Security

### Agent Behavior Constraints
- Implement content safety filters
- Set reasonable action limits per agent
- Monitor for suspicious behavior patterns
- Use the enhanced loop detection system

### Multi-Agent Security
- Isolate agent memory spaces
- Prevent cross-agent data leakage
- Validate inter-agent communications
- Monitor for coordinated malicious behavior

### Simulation State Protection
- Validate simulation states before restoration
- Use checksums for cache integrity
- Prevent state tampering through input validation
- Implement state rollback mechanisms

## Network Security

### API Communication
- Use TLS/SSL for all API communications
- Validate SSL certificates
- Implement request timeouts
- Use connection pooling safely

### Rate Limiting and Throttling
```python
# Example rate limiting configuration
MAX_REQUESTS_PER_MINUTE = 60
EXPONENTIAL_BACKOFF_FACTOR = 5
```

### Proxy and Firewall Considerations
- Configure proxies securely if required
- Allow only necessary outbound connections
- Monitor for unusual network patterns
- Use VPN for sensitive environments

## Content Safety

### Harmful Content Prevention
- Enable RAI (Responsible AI) content filters
- Implement custom content validation
- Monitor outputs for policy violations
- Have human review processes for sensitive applications

### Copyright and Intellectual Property
- Enable copyright infringement prevention
- Avoid generating copyrighted content
- Implement attribution where required
- Review outputs for IP violations

## Deployment Security

### Production Environment
```bash
# Environment setup for production
export PYTHONPATH=/path/to/tinytroupe
export TINYTROUPE_ENV=production
export LOG_LEVEL=WARNING  # Reduce verbose logging
```

### Container Security
```dockerfile
# Example secure Dockerfile patterns
FROM python:3.11-slim
USER nobody  # Don't run as root
COPY --chown=nobody:nobody . /app
```

### Monitoring and Alerting
- Monitor for unusual API usage patterns
- Set up alerts for error rate spikes
- Track memory and CPU usage
- Log security-relevant events

## Incident Response

### Security Event Detection
- Monitor logs for error patterns
- Track unusual agent behaviors
- Watch for resource exhaustion
- Alert on authentication failures

### Response Procedures
1. **Immediate**: Stop affected simulations
2. **Assessment**: Analyze logs and determine impact
3. **Containment**: Isolate affected components
4. **Recovery**: Restore from clean state
5. **Lessons**: Update security measures

## Security Checklist

### Before Deployment
- [ ] API keys stored securely in environment variables
- [ ] Configuration validation enabled
- [ ] Input sanitization implemented
- [ ] Error handling configured securely
- [ ] Resource limits set appropriately
- [ ] Monitoring and logging configured
- [ ] Content safety filters enabled

### Regular Security Maintenance
- [ ] Update dependencies regularly
- [ ] Rotate API keys periodically
- [ ] Review and audit configurations
- [ ] Monitor for security advisories
- [ ] Update security documentation
- [ ] Conduct security testing

### Incident Response Preparedness
- [ ] Incident response plan documented
- [ ] Contact information current
- [ ] Backup and recovery procedures tested
- [ ] Monitoring and alerting functional
- [ ] Team training completed

## Resources and References

### Security Tools
- Static analysis: `bandit`, `safety`
- Dependency scanning: `pip-audit`
- Secret detection: `detect-secrets`
- Code quality: `pylint`, `flake8`

### External Resources
- [OWASP Security Guidelines](https://owasp.org/)
- [OpenAI Security Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)
- [Azure OpenAI Security](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/concepts/security)

### Internal Documentation
- [TinyTroupe Configuration Guide](README.md)
- [Error Handling Documentation](tinytroupe/exceptions.py)
- [Performance Guidelines](PERFORMANCE_ANALYSIS.md)

## Contact and Support

For security issues or questions:
- Review existing security documentation
- Check GitHub issues for known problems
- Follow responsible disclosure for security vulnerabilities
- Contact maintainers through official channels

Remember: Security is an ongoing process, not a one-time setup. Regular review and updates are essential for maintaining a secure TinyTroupe deployment.