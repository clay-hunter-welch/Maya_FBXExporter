FBXExporter : coded as a follow-along course, currently being debugged and modified to work on joint and mesh heirarchies other than
the configuration used in the course.  Assumptions for current use:
1) Works on single-level referenced characters only--not on characters without namespace, and not on characters with nested reference
2) Works on characters where bind mesh is located within the joint heirarchy where the origin joint is located.  Geo outside that
heirarchy is not considered.

As it stands, the tool will export properly configured models in FBX format as:
1) static with no anim
2) in worldspace with anim (subrange supported)
3) character origin moved to world origin with anim (subrange supported)
4) character zeroed on world origin with anim, as for weapon anim (subrange supported)

The tool is nondestructive and exports a mesh bound to a joint heirarchy scrubbed of namespace for reference elsewhere, accomplishing 
this by cleverly exploiting the fact that a duplicated joint network is cleaned of namespace.  The bind mesh is temporarily connected
to this duplicate network, the export occurs, the mesh is reconnected to the original network and the duplicate is deleted, leaving the
file undamaged.