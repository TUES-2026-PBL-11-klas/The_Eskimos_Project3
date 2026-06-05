# Remote state in DigitalOcean Spaces (S3-compatible). Spaces is not AWS, so the AWS S3
# backend needs several validations skipped. Credentials are NOT stored here — pass them as
# environment variables before `terraform init`:
#
#   $env:AWS_ACCESS_KEY_ID     = "<spaces access key>"
#   $env:AWS_SECRET_ACCESS_KEY = "<spaces secret>"
#
# The bucket/region below must match the Space you created (Part 1.1 §2). If your Space is in
# a different region, change `region` and the `endpoints.s3` host (e.g. ams3, nyc3, sgp1).
terraform {
  backend "s3" {
    bucket = "eventhub-tfstate"
    key    = "eventhub/terraform.tfstate"
    region = "fra1"

    endpoints = {
      s3 = "https://fra1.digitaloceanspaces.com"
    }

    # DO Spaces is S3-compatible but not AWS — skip AWS-only checks.
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
    use_path_style              = true
  }
}
