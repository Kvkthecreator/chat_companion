import { OnboardingSubmitSchema } from '@/shared/contracts/onboarding';

describe('OnboardingSubmitSchema', () => {
  it('accepts valid data', () => {
    const data = {
      basket_id: '00000000-0000-0000-0000-000000000000',
      name: 'Alice',
      tension: 't',
      aspiration: 'a',
    };
    expect(OnboardingSubmitSchema.parse(data)).toBeTruthy();
  });

  it('rejects invalid data', () => {
    const result = OnboardingSubmitSchema.safeParse({});
    expect(result.success).toBeFalsy();
  });
});
