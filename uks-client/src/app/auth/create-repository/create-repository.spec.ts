import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateRepository } from './create-repository';

describe('CreateRepository', () => {
  let component: CreateRepository;
  let fixture: ComponentFixture<CreateRepository>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CreateRepository]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CreateRepository);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
