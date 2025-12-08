#!/bin/bash
set -e

echo "🔧 Fixing legacy @/types imports..."

# Fix common import patterns
find web -name "*.ts" -o -name "*.tsx" | xargs sed -i '' 's|from "@/types"|from "@shared/contracts"|g'
find web -name "*.ts" -o -name "*.tsx" | xargs sed -i '' 's|import type { Document } from "@shared/contracts"|import type { DocumentDTO } from "@shared/contracts/documents"|g'
find web -name "*.ts" -o -name "*.tsx" | xargs sed -i '' 's|import type { Block } from "@shared/contracts"|import type { BlockDTO } from "@shared/contracts/documents"|g'
find web -name "*.ts" -o -name "*.tsx" | xargs sed -i '' 's|import type { Basket } from "@shared/contracts"|import type { Basket } from "@shared/contracts/baskets"|g'
find web -name "*.ts" -o -name "*.tsx" | xargs sed -i '' 's|import type { Dump } from "@shared/contracts"|import type { Dump } from "@shared/contracts/dumps"|g'

# Fix specific type usage
find web -name "*.ts" -o -name "*.tsx" | xargs sed -i '' 's|: Document\[\]|: DocumentDTO[]|g'
find web -name "*.ts" -o -name "*.tsx" | xargs sed -i '' 's|: Document |: DocumentDTO |g'
find web -name "*.ts" -o -name "*.tsx" | xargs sed -i '' 's|<Document>|<DocumentDTO>|g'
find web -name "*.ts" -o -name "*.tsx" | xargs sed -i '' 's|<Document\[\]>|<DocumentDTO[]>|g'

echo "✅ Legacy imports fixed!"