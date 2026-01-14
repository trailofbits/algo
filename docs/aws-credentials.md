# AWS Credential Configuration

Algo supports multiple methods for providing AWS credentials, following standard AWS practices:

## Methods (in order of precedence)

1. **Command-line variables** (highest priority)
   ```bash
   ./algo -e "aws_access_key=YOUR_KEY aws_secret_key=YOUR_SECRET"
   ```

2. **Environment variables**
   ```bash
   export AWS_ACCESS_KEY_ID=YOUR_KEY
   export AWS_SECRET_ACCESS_KEY=YOUR_SECRET
   export AWS_SESSION_TOKEN=YOUR_TOKEN  # Optional, for temporary credentials
   ./algo
   ```

3. **AWS credentials file** (lowest priority)
   - Default location: `~/.aws/credentials`
   - Custom location: Set `AWS_SHARED_CREDENTIALS_FILE` environment variable
   - Profile selection: Set `AWS_PROFILE` environment variable (defaults to "default")

## Using AWS Credentials File

After running `aws configure` or manually creating `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = YOUR_KEY_ID
aws_secret_access_key = YOUR_SECRET_KEY

[work]
aws_access_key_id = WORK_KEY_ID
aws_secret_access_key = WORK_SECRET_KEY
aws_session_token = TEMPORARY_TOKEN  # Optional
```

To use a specific profile:
```bash
AWS_PROFILE=work ./algo
```

## Security Considerations

- Credentials files should have restricted permissions (600)
- Consider using AWS IAM roles or temporary credentials when possible
- Tools like [aws-vault](https://github.com/99designs/aws-vault) can provide additional security by storing credentials encrypted

## Troubleshooting

If Algo isn't finding your credentials:

1. Check file permissions: `ls -la ~/.aws/credentials`
2. Verify the profile name matches: `AWS_PROFILE=your-profile`
3. Test with AWS CLI: `aws sts get-caller-identity`

If credentials are found but authentication fails:
- Ensure your IAM user has the required permissions (see [EC2 deployment guide](deploy-from-ansible.md))
- Check if you need session tokens for temporary credentials
