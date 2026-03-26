# Operations Guide

## Daily Operations

### Monitoring Health

```bash
# Check service status
make health-check

# View metrics
make metrics

# Check logs
make compose-logs
```

### Common Tasks

**Restart service:**
```bash
make compose-down
make compose-up
```

**Update policies:**
```bash
make ingest-policies
make compose-restart
```

**Backup data:**
```bash
make backup-chroma
```

## Incident Response

### High Error Rate

1. Check logs: `make compose-logs`
2. Verify API keys are valid
3. Check OpenAI API status
4. Review recent changes

### High Latency

1. Check metrics for bottlenecks
2. Increase replicas if needed
3. Review diff sizes being processed
4. Consider caching strategies

### Out of Memory

1. Check container memory usage
2. Reduce `WEBHOOK_MAX_DIFF_CHARS`
3. Increase container limits
4. Review Chroma index size

## Maintenance

### Weekly Tasks

- Review cost metrics
- Check error logs
- Update dependencies
- Backup Chroma index

### Monthly Tasks

- Security updates
- Performance review
- Cost optimization
- Policy updates

## Troubleshooting

See DEPLOYMENT.md for detailed troubleshooting guide.
