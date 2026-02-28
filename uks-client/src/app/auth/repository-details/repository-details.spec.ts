import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RepositoryDetails } from './repository-details';
import { ProjectService } from '../../services/project';
import { UserService } from '../../services/user';
import { of, throwError } from 'rxjs';

describe('RepositoryDetails', () => {
  let component: RepositoryDetails;
  let fixture: ComponentFixture<RepositoryDetails>;
  let projectSpy: jasmine.SpyObj<ProjectService>;
  let userSpy: jasmine.SpyObj<UserService>;

  const mockRepo = {
    id: 1,
    name: 'test-repo',
    visibility: 'public',
    badge: 'NONE',
    owner_username: 'owner'
  };

  beforeEach(async () => {
    projectSpy = jasmine.createSpyObj('ProjectService', [
      'getProjectTags',
      'getCollaborators',
      'addCollaborator',
      'removeCollaborators',
      'removeTag',
      'addTag',
      'editVisibilityRepository',
      'deleteRepository',
      'updateBadgeRepository'
    ]);

    userSpy = jasmine.createSpyObj('UserService', [
      'getCurrentUser',
      'filterUserByText',
      'isSuperAdmin'
    ]);

    userSpy.getCurrentUser.and.returnValue({ username: 'owner' });
    userSpy.isSuperAdmin.and.returnValue(false);

    await TestBed.configureTestingModule({
      imports: [RepositoryDetails],
      providers: [
        { provide: ProjectService, useValue: projectSpy },
        { provide: UserService, useValue: userSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RepositoryDetails);
    component = fixture.componentInstance;
    component.repository = mockRepo;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should init and load data', () => {
    projectSpy.getProjectTags.and.returnValue(of([]));
    projectSpy.getCollaborators.and.returnValue(of([]));

    component.ngOnInit();

    expect(component.selectedBadge).toBe('NONE');
    expect(projectSpy.getProjectTags).toHaveBeenCalled();
    expect(projectSpy.getCollaborators).toHaveBeenCalled();
  });

  it('should switch tab', () => {
    component.setTab('tags');
    expect(component.activeTab).toBe('tags');
  });

  it('should load tags and set lastTag', () => {
    const tags = [
      { id: 1, updated_at: '2024-01-01' },
      { id: 2, updated_at: '2025-01-01' }
    ];

    projectSpy.getProjectTags.and.returnValue(of(tags));

    component.loadTags();

    expect(component.tags.length).toBe(2);
    expect(component.lastTag.id).toBe(2);
  });

  it('should load collaborators', () => {
    const users = [{ id: 1, username: 'a' }];
    projectSpy.getCollaborators.and.returnValue(of(users));

    component.loadCollaborators();

    expect(component.collaborators.length).toBe(1);
  });

  it('should add collaborator', () => {
    component.selectedUser = { id: 2, username: 'new' };
    projectSpy.addCollaborator.and.returnValue(of({}));

    component.addCollaborator();

    expect(component.collaborators[0].username).toBe('new');
  });

  it('should remove collaborator', () => {
    component.collaborators = [{ id: 1 }, { id: 2 }];
    projectSpy.removeCollaborators.and.returnValue(of({}));

    component.removeCollaborators({ id: 1 });

    expect(component.collaborators.length).toBe(1);
  });

  it('should add tag', () => {
    const tag = { id: 99 };
    projectSpy.addTag.and.returnValue(of(tag));

    component.addTag();

    expect(component.tags[0].id).toBe(99);
  });

  it('should remove tag', () => {
    component.tags = [{ id: 1 }, { id: 2 }];
    projectSpy.removeTag.and.returnValue(of({}));

    component.removeTag({ id: 1 });

    expect(component.tags.length).toBe(1);
  });

  it('should detect owner', () => {
    projectSpy.getProjectTags.and.returnValue(of([]));
    projectSpy.getCollaborators.and.returnValue(of([]));

    component.ngOnInit();

    expect(component.isOwner()).toBeTrue();
  });

  it('should toggle visibility type', () => {
    component.repository.visibility = 'public';
    expect(component.getTypeVisibility()).toBe('private');
  });

  it('should change visibility after modal ok', () => {
    projectSpy.editVisibilityRepository.and.returnValue(of({}));

    component.globalType = 'visibility';
    component.onModalOk();

    expect(projectSpy.editVisibilityRepository).toHaveBeenCalled();
  });

  it('should delete repo', () => {
    projectSpy.deleteRepository.and.returnValue(of({}));

    component.globalType = 'delete';
    component.onModalOk();

    expect(projectSpy.deleteRepository).toHaveBeenCalled();
  });

  it('should update badge', () => {
    projectSpy.updateBadgeRepository.and.returnValue(of({}));

    component.globalType = 'accepted';
    component.selectedBadge = 'VERIFIED';
    component.onModalOk();

    expect(projectSpy.updateBadgeRepository).toHaveBeenCalledWith(1, 'VERIFIED');
  });

  it('should search users', () => {
    userSpy.filterUserByText.and.returnValue(of([{ username: 'john' }]));
    component.searchTerm = 'jo';

    component.onSearchUser();

    expect(component.filteredUsers.length).toBe(1);
  });

  it('should clear search if term < 2', () => {
    component.searchTerm = 'a';
    component.filteredUsers = [{ username: 'x' }];

    component.onSearchUser();

    expect(component.filteredUsers.length).toBe(0);
  });

  it('should select user', () => {
    const u = { id: 1 };
    component.selectUser(u);

    expect(component.selectedUser).toBe(u);
    expect(component.filteredUsers.length).toBe(0);
  });

  it('should generate random string length', () => {
    const str = component.generateRandomString(6);
    expect(str.length).toBe(6);
  });

  it('should generate random number range', () => {
    const num = (component as any).getRandomNumber();
    expect(num).toBeGreaterThanOrEqual(1);
    expect(num).toBeLessThanOrEqual(200);
  });
});