const { createClient } = require('@supabase/supabase-js');

async function checkQueue() {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL, 
    process.env.SUPABASE_SERVICE_ROLE_KEY
  );

  console.log('🔍 Checking agent queue status...');
  
  // Check raw dumps queue
  const { data: queueData, error: queueError } = await supabase
    .from('agent_queue')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(10);
  
  if (queueError) {
    console.error('❌ Queue query error:', queueError);
    return;
  }
  
  console.log('📊 Recent queue entries:');
  queueData.forEach((entry, i) => {
    console.log(`  ${i+1}. ID: ${entry.id} | State: ${entry.processing_state} | Dump: ${entry.dump_id?.substring(0,8)}...`);
    console.log(`     Worker: ${entry.worker_id || 'none'} | Error: ${entry.error_message || 'none'}`);
    console.log(`     Created: ${entry.created_at} | Updated: ${entry.updated_at}`);
    console.log('');
  });
  
  // Check queue stats
  const { data: stats, error: statsError } = await supabase.rpc('fn_queue_health');
  if (!statsError && stats) {
    console.log('📈 Queue Health Stats:');
    stats.forEach(stat => {
      console.log(`  ${stat.processing_state}: ${stat.count}`);
    });
  } else if (statsError) {
    console.error('❌ Stats error:', statsError);
  }
}

checkQueue().catch(console.error);