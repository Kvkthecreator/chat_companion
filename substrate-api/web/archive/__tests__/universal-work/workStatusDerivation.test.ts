/**
 * Work Status Derivation Tests - Canon v2.2
 * 
 * Tests the derivation of work statuses from processing states and governance decisions.
 * Validates real-time status updates and user-facing status display logic.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { UniversalWorkTestCase, TestDataFactory } from './UniversalWorkTestBase';

describe('Work Status Derivation - Canon v2.2', () => {
  let testCase: UniversalWorkTestCase;

  beforeEach(() => {
    testCase = new UniversalWorkTestCase();
  });

  describe('Status Mapping Logic', () => {
    it('should map processing states to user-facing statuses correctly', () => {
      const statusMappings = [
        { processing_state: 'pending', execution_mode: 'create_proposal', expected: 'awaiting_review' },
        { processing_state: 'claimed', execution_mode: 'auto_execute', expected: 'processing' },
        { processing_state: 'running', execution_mode: 'auto_execute', expected: 'processing' },
        { processing_state: 'completed', execution_mode: 'auto_execute', expected: 'completed' },
        { processing_state: 'failed', execution_mode: 'auto_execute', expected: 'failed' },
        { processing_state: 'pending', execution_mode: 'create_proposal', expected: 'awaiting_review' }
      ];

      statusMappings.forEach(({ processing_state, execution_mode, expected }) => {
        const workStatus = testCase.createMockWorkStatus('work-123', processing_state);
        workStatus.execution_mode = execution_mode;
        
        const userFacingStatus = deriveUserFacingStatus(workStatus);
        expect(userFacingStatus).toBe(expected);
      });
    });

    it('should handle proposal-based work status derivation', () => {
      const proposalStatuses = [
        { proposal_status: 'pending', expected: 'awaiting_review' },
        { proposal_status: 'approved', processing_state: 'pending', expected: 'approved_pending' },
        { proposal_status: 'approved', processing_state: 'running', expected: 'processing' },
        { proposal_status: 'rejected', expected: 'rejected' },
        { proposal_status: 'cancelled', expected: 'cancelled' }
      ];

      proposalStatuses.forEach(({ proposal_status, processing_state, expected }) => {
        const workStatus = testCase.createMockWorkStatus('work-123', processing_state || 'pending');
        workStatus.execution_mode = 'create_proposal';
        workStatus.proposal_status = proposal_status;
        
        const userFacingStatus = deriveUserFacingStatus(workStatus);
        expect(userFacingStatus).toBe(expected);
      });
    });
  });

  describe('Status Priority and Precedence', () => {
    it('should prioritize error states over normal flow', () => {
      const workStatus = testCase.createMockWorkStatus('work-123', 'failed');
      workStatus.execution_mode = 'auto_execute';
      workStatus.error_message = 'Processing failed';
      
      const userFacingStatus = deriveUserFacingStatus(workStatus);
      expect(userFacingStatus).toBe('failed');
    });

    it('should show user override information in status', () => {
      const workStatus = testCase.createMockWorkStatus('work-123', 'completed');
      workStatus.work_payload = {
        operations: [],
        basket_id: 'test-basket',
        user_override: 'allow_auto'
      };
      
      const statusDetails = deriveStatusDetails(workStatus);
      expect(statusDetails.user_override).toBe('allow_auto');
      expect(statusDetails.governance_bypassed).toBe(true);
    });

    it('should include confidence information in status details', () => {
      const workStatus = testCase.createMockWorkStatus('work-123', 'completed');
      workStatus.work_payload = {
        operations: [],
        basket_id: 'test-basket',
        confidence_score: 0.92
      };
      workStatus.governance_policy = { mode: 'confidence', confidence_threshold: 0.8 };
      
      const statusDetails = deriveStatusDetails(workStatus);
      expect(statusDetails.confidence_score).toBe(0.92);
      expect(statusDetails.confidence_met_threshold).toBe(true);
    });
  });

  describe('Real-time Status Updates', () => {
    it('should detect status changes for real-time updates', () => {
      const previousStatus = testCase.createMockWorkStatus('work-123', 'pending');
      const currentStatus = testCase.createMockWorkStatus('work-123', 'running');
      
      const hasChanged = detectStatusChange(previousStatus, currentStatus);
      expect(hasChanged).toBe(true);
    });

    it('should not trigger updates for identical statuses', () => {
      const status1 = testCase.createMockWorkStatus('work-123', 'running');
      const status2 = testCase.createMockWorkStatus('work-123', 'running');
      
      const hasChanged = detectStatusChange(status1, status2);
      expect(hasChanged).toBe(false);
    });

    it('should detect progress updates within same state', () => {
      const status1 = testCase.createMockWorkStatus('work-123', 'running');
      status1.progress_percent = 25;
      
      const status2 = testCase.createMockWorkStatus('work-123', 'running');
      status2.progress_percent = 75;
      
      const hasChanged = detectStatusChange(status1, status2);
      expect(hasChanged).toBe(true);
    });
  });

  describe('Work Type Status Specialization', () => {
    TestDataFactory.workTypes.forEach(workType => {
      it(`should handle ${workType} specific status information`, () => {
        const workStatus = testCase.createMockWorkStatus('work-123', 'running');
        workStatus.work_type = workType;
        
        const statusDetails = deriveStatusDetails(workStatus);
        
        // Each work type should have specific status context
        expect(statusDetails.work_type).toBe(workType);
        expect(statusDetails.description).toBeDefined();
        
        // P0_CAPTURE should show capture progress
        if (workType === 'P0_CAPTURE') {
          expect(statusDetails.description).toContain('Capturing');
        }
        
        // P1_SUBSTRATE should show substrate operations
        if (workType === 'P1_SUBSTRATE') {
          expect(statusDetails.description).toContain('Processing');
        }
        
        // MANUAL_EDIT should show user context
        if (workType === 'MANUAL_EDIT') {
          expect(statusDetails.user_initiated).toBe(true);
        }
        
        // PROPOSAL_REVIEW should show review context
        if (workType === 'PROPOSAL_REVIEW') {
          expect(statusDetails.requires_user_action).toBe(true);
        }
      });
    });
  });

  describe('Batch Status Processing', () => {
    it('should efficiently process multiple work statuses', () => {
      const workStatuses = Array.from({ length: 50 }, (_, i) => 
        testCase.createMockWorkStatus(`work-${i}`, 'running')
      );
      
      const batchResult = processBatchStatuses(workStatuses);
      
      expect(batchResult.processed_count).toBe(50);
      expect(batchResult.by_status.processing).toBe(50);
      expect(batchResult.total_processing).toBe(50);
    });

    it('should aggregate status counts correctly', () => {
      const workStatuses = [
        testCase.createMockWorkStatus('work-1', 'pending'),
        testCase.createMockWorkStatus('work-2', 'running'),
        testCase.createMockWorkStatus('work-3', 'running'),
        testCase.createMockWorkStatus('work-4', 'completed'),
        testCase.createMockWorkStatus('work-5', 'failed')
      ];
      
      const batchResult = processBatchStatuses(workStatuses);
      
      expect(batchResult.by_status.queued).toBe(1);
      expect(batchResult.by_status.processing).toBe(2);
      expect(batchResult.by_status.completed).toBe(1);
      expect(batchResult.by_status.failed).toBe(1);
    });
  });

  describe('Error Status Handling', () => {
    it('should provide detailed error information', () => {
      const workStatus = testCase.createMockWorkStatus('work-123', 'failed');
      workStatus.error_message = 'Validation failed: Invalid basket ID';
      workStatus.error_code = 'VALIDATION_ERROR';
      workStatus.retry_count = 2;
      workStatus.max_retries = 3;
      
      const statusDetails = deriveStatusDetails(workStatus);
      
      expect(statusDetails.error_message).toBe('Validation failed: Invalid basket ID');
      expect(statusDetails.error_code).toBe('VALIDATION_ERROR');
      expect(statusDetails.can_retry).toBe(true);
      expect(statusDetails.retry_count).toBe(2);
    });

    it('should indicate when max retries exceeded', () => {
      const workStatus = testCase.createMockWorkStatus('work-123', 'failed');
      workStatus.retry_count = 3;
      workStatus.max_retries = 3;
      
      const statusDetails = deriveStatusDetails(workStatus);
      
      expect(statusDetails.can_retry).toBe(false);
      expect(statusDetails.permanent_failure).toBe(true);
    });
  });
});

// Mock helper functions that would be implemented in the actual status system
function deriveUserFacingStatus(workStatus: any): string {
  if (workStatus.processing_state === 'failed') return 'failed';
  
  if (workStatus.execution_mode === 'create_proposal') {
    if (workStatus.proposal_status === 'pending') return 'awaiting_review';
    // Default to awaiting_review when proposal mode but proposal_status absent
    if (!workStatus.proposal_status && workStatus.processing_state === 'pending') return 'awaiting_review';
    if (workStatus.proposal_status === 'approved') {
      return workStatus.processing_state === 'pending' ? 'approved_pending' : 'processing';
    }
    if (workStatus.proposal_status === 'rejected') return 'rejected';
    if (workStatus.proposal_status === 'cancelled') return 'cancelled';
  }
  
  if (workStatus.processing_state === 'pending') return 'queued';
  if (workStatus.processing_state === 'claimed' || workStatus.processing_state === 'running') return 'processing';
  if (workStatus.processing_state === 'completed') return 'completed';
  
  return 'unknown';
}

function deriveStatusDetails(workStatus: any): any {
  const details = {
    work_type: workStatus.work_type,
    description: getWorkTypeDescription(workStatus.work_type),
    user_initiated: workStatus.work_type === 'MANUAL_EDIT',
    requires_user_action: workStatus.work_type === 'PROPOSAL_REVIEW',
    governance_bypassed: workStatus.work_payload?.user_override === 'allow_auto',
    confidence_score: workStatus.work_payload?.confidence_score,
    confidence_met_threshold: false,
    user_override: workStatus.work_payload?.user_override,
    error_message: workStatus.error_message,
    error_code: workStatus.error_code,
    can_retry: workStatus.retry_count < workStatus.max_retries,
    retry_count: workStatus.retry_count,
    permanent_failure: workStatus.retry_count >= workStatus.max_retries
  };
  
  if (details.confidence_score && workStatus.governance_policy?.confidence_threshold) {
    details.confidence_met_threshold = details.confidence_score >= workStatus.governance_policy.confidence_threshold;
  }
  
  return details;
}

function getWorkTypeDescription(workType: string): string {
  const descriptions = {
    'P0_CAPTURE': 'Capturing user input',
    'P1_SUBSTRATE': 'Processing substrate operations', 
    'P2_GRAPH': 'Building knowledge graph',
    'P3_REFLECTION': 'Creating reflections',
    'P4_COMPOSE': 'Composing documents',
    'MANUAL_EDIT': 'Manual user edit',
    'PROPOSAL_REVIEW': 'Awaiting proposal review',
    'TIMELINE_RESTORE': 'Restoring timeline state'
  };
  return descriptions[workType] || 'Processing work';
}

function detectStatusChange(previous: any, current: any): boolean {
  return previous.processing_state !== current.processing_state ||
         previous.progress_percent !== current.progress_percent ||
         previous.proposal_status !== current.proposal_status;
}

function processBatchStatuses(workStatuses: any[]): any {
  const by_status = {};
  let total_processing = 0;
  
  workStatuses.forEach(status => {
    const userStatus = deriveUserFacingStatus(status);
    by_status[userStatus] = (by_status[userStatus] || 0) + 1;
    
    if (userStatus === 'processing' || userStatus === 'queued') {
      total_processing++;
    }
  });
  
  return {
    processed_count: workStatuses.length,
    by_status,
    total_processing
  };
}
