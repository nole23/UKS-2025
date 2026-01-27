import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DefautlPrivateRepository } from './defautl-private-repository';

describe('DefautlPrivateRepository', () => {
  let component: DefautlPrivateRepository;
  let fixture: ComponentFixture<DefautlPrivateRepository>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DefautlPrivateRepository]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DefautlPrivateRepository);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
