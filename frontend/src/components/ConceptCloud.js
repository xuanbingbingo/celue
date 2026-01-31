import React from 'react';

function ConceptCloud({ concepts, activeConcept, onConceptClick }) {
  if (concepts.length === 0) return null;

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-5 mb-5 shadow-xl">
      <h3 className="text-sm font-semibold text-gray-600 mb-3">🏷️ 概念板块</h3>
      <div className="flex flex-wrap gap-2">
        {concepts.map(concept => {
          const isActive = activeConcept === concept;
          return (
            <span
              key={concept}
              onClick={(e) => {
                e.stopPropagation();
                onConceptClick(concept);
              }}
              className={`
                px-3 py-1.5 rounded-full text-xs font-medium cursor-pointer
                transition-all duration-200
                ${isActive 
                  ? 'bg-gradient-to-r from-sky-500 to-sky-600 text-white shadow-md' 
                  : 'bg-gradient-to-r from-sky-50 to-sky-100 text-sky-700 hover:-translate-y-0.5 hover:shadow-md'
                }
              `}
            >
              {concept}
            </span>
          );
        })}
      </div>
    </div>
  );
}

export default ConceptCloud;
