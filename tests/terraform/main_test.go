package main

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
    "github.com/gruntwork-io/terratest/modules/gcp"
)

func TestGKEClusterCreation(t *testing.T) {
    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../../terraform",
        Vars: map[string]interface{}{
            "project_id": "ethereum-test-node-1752961365",
            "region":     "us-central1",
            "cluster_name": "ethereum-cluster-test",
        },
    })
    
    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)
    
    // Проверка создания кластера
    clusterName := terraform.Output(t, terraformOptions, "cluster_name")
    assert.NotEmpty(t, clusterName)
    assert.Equal(t, "ethereum-cluster-test", clusterName)
    
    // Проверка endpoint
    clusterEndpoint := terraform.Output(t, terraformOptions, "cluster_endpoint")
    assert.NotEmpty(t, clusterEndpoint)
}

func TestGKEClusterSecurity(t *testing.T) {
    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../../terraform",
        Vars: map[string]interface{}{
            "project_id": "ethereum-test-node-1752961365",
            "region":     "us-central1",
        },
    })
    
    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)
    
    // Проверка включения Network Policy
    clusterName := terraform.Output(t, terraformOptions, "cluster_name")
    cluster := gcp.GetGkeCluster(t, clusterName, "us-central1", "ethereum-test-node-1752961365")
    
    // Проверка что Network Policy включен
    assert.True(t, cluster.NetworkPolicy.Enabled)
    assert.Equal(t, "CALICO", cluster.NetworkPolicy.Provider)
}

func TestStorageBucketCreation(t *testing.T) {
    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../../terraform",
        Vars: map[string]interface{}{
            "project_id": "ethereum-test-node-1752961365",
            "region":     "us-central1",
        },
    })
    
    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)
    
    // Проверка создания storage bucket
    bucketName := terraform.Output(t, terraformOptions, "storage_bucket_name")
    assert.NotEmpty(t, bucketName)
    
    // Проверка что bucket существует
    bucket := gcp.GetStorageBucket(t, bucketName)
    assert.NotNil(t, bucket)
} 