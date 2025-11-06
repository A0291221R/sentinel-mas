fetch_ssm_config() {
    local param_path=$1
    local param_name=$2
    
    echo "📥 Fetching $param_name..."
    
    if aws sts get-caller-identity &>/dev/null; then
        CONFIG=$(aws ssm get-parameter \
            --name "$param_path" \
            --with-decryption \
            --query 'Parameter.Value' \
            --output text 2>/dev/null)
        
        if [ $? -eq 0 ] && [ -n "$CONFIG" ]; then
            # Convert spaces to newlines if no newlines exist
            if [[ "$CONFIG" != *$'\n'* ]]; then
                CONFIG=$(echo "$CONFIG" | tr ' ' '\n')
            fi
            
            # Export each key=value pair
            while IFS='=' read -r key value; do
                [ -n "$key" ] && export "$key=$value"
            done <<< "$CONFIG"
            
            echo "✅ Loaded $param_name"
            return 0
        else
            echo "⚠️  Could not fetch $param_name"
            return 1
        fi
    else
        echo "⚠️  No AWS credentials for $param_name"
        return 1
    fi
}
