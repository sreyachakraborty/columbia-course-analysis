'''
Scrape CS courses offered in Spring 2026 from Columbia SIS
'''

import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_spring_2026_cs_courses():
    """Scrape CS courses offered in Spring 2026 from SIS"""
    
    url = "https://doc.sis.columbia.edu/sel/COMS_Spring2026.html"
    
    print("Fetching Spring 2026 CS courses from SIS...")
    
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    courses = []
    current_course = None
    
    # Find all rows in the course listing table
    table = soup.find('table', class_='course-listing')
    rows = table.find_all('tr') if table else []
    
    for row in rows:
        # Check if this is a course header row (has th with course info)
        header = row.find('th')
        if header:
            # Parse course header: "Spring 2026 Computer Science W3157\nADVANCED PROGRAMMING"
            header_text = header.get_text(separator='\n').strip()
            lines = header_text.split('\n')
            
            # Extract course code (e.g., "W3157", "E6998")
            code_match = re.search(r'([A-Z]+\s*)?([WE]\d{4})', lines[0])
            if code_match:
                # Get department prefix
                dept_match = re.search(r'(Computer Science|Engineering|Operations Research)', lines[0])
                dept = 'COMS'
                if 'Electrical Engineering' in lines[0]:
                    dept = 'CSEE'
                elif 'Operations Research' in lines[0]:
                    dept = 'CSOR'
                elif 'Biomedical' in lines[0]:
                    dept = 'CBMF'
                elif 'Engineering E' in lines[0]:
                    dept = 'ENGI'
                
                course_code = f"{dept} {code_match.group(2)}"
                course_name = lines[1] if len(lines) > 1 else ''
                
                current_course = {
                    'course_code': course_code,
                    'name': course_name,
                    'sections': []
                }
                courses.append(current_course)
        
        # Check if this is a section row (has course-details)
        details = row.find('div', class_='course-details')
        if details and current_course:
            section_info = {}
            
            # Get section number from link
            section_link = row.find('a')
            if section_link:
                section_match = re.search(r'Section (\d+)', section_link.get_text())
                if section_match:
                    section_info['section'] = section_match.group(1)
            
            # Parse dl/dt/dd pairs
            dl = details.find('dl')
            if dl:
                # Get topic name if exists (for W4995/E6998)
                h1 = dl.find('h1')
                if h1:
                    section_info['topic'] = h1.get_text(strip=True)
                
                dts = dl.find_all('dt')
                dds = dl.find_all('dd')
                
                for dt, dd in zip(dts, dds):
                    key = dt.get_text(strip=True).rstrip(':').lower()
                    value = dd.get_text(strip=True)
                    
                    if 'call number' in key:
                        section_info['call_number'] = value
                    elif 'points' in key:
                        section_info['points'] = value
                    elif 'day/time' in key:
                        section_info['day_time'] = value
                    elif 'location' in key:
                        section_info['location'] = value
                    elif 'enrollment' in key:
                        # Parse "43 students (189 max)"
                        enroll_match = re.search(r'(\d+)\s*student', value)
                        max_match = re.search(r'\((\d+)\s*max\)', value)
                        section_info['enrolled'] = int(enroll_match.group(1)) if enroll_match else 0
                        section_info['max_enrollment'] = int(max_match.group(1)) if max_match else 0
                        section_info['full'] = 'Full' in value
                    elif 'instructor' in key:
                        section_info['instructor'] = value
                    elif 'notes' in key:
                        section_info['notes'] = value
            
            current_course['sections'].append(section_info)
    
    print(f"Found {len(courses)} unique courses")
    
    # Save full data
    with open("spring_2026_cs_courses.json", "w") as f:
        json.dump(courses, f, indent=4)
    
    # Create simplified version (unique courses with instructors)
    simplified = []
    for course in courses:
        instructors = list(set(
            s.get('instructor', '') for s in course['sections'] if s.get('instructor')
        ))
        
        simplified.append({
            'course_code': course['course_code'],
            'name': course['name'],
            'instructors': instructors,
            'num_sections': len(course['sections']),
            'topics': list(set(s.get('topic', '') for s in course['sections'] if s.get('topic')))
        })
    
    with open("spring_2026_cs_courses_simple.json", "w") as f:
        json.dump(simplified, f, indent=4)
    
    print("Saved to spring_2026_cs_courses.json (full) and spring_2026_cs_courses_simple.json (simplified)")
    
    # Print preview
    print("\n" + "=" * 60)
    print("SPRING 2026 CS COURSES")
    print("=" * 60)
    for course in simplified:
        instructors = ', '.join(course['instructors']) if course['instructors'] else 'TBA'
        topics = f" ({', '.join(course['topics'])})" if course['topics'] else ''
        print(f"{course['course_code']}: {course['name']}{topics}")
        print(f"    Instructors: {instructors}")
        print()
    
    return courses


if __name__ == "__main__":
    courses = scrape_spring_2026_cs_courses()